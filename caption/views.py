from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import io
import base64
import httpx
import os
import threading
import json
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

_blip_lock = threading.Lock()
_blip_loaded = False
_blip_processor = None
_blip_model = None

# Environment variables
VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL")
VLLM_API_KEY = os.environ.get("VLLM_API_KEY")
VLLM_MODEL = os.environ.get("VLLM_MODEL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load BLIP
def _load_blip_if_needed():
    global _blip_loaded, _blip_processor, _blip_model
    if _blip_loaded:
        return
    with _blip_lock:
        if _blip_loaded:
            return
        from transformers import BlipProcessor, BlipForConditionalGeneration
        _blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        _blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        _blip_model.eval()
        _blip_loaded = True

def _caption_with_blip(pil_image: Image.Image) -> str:
    _load_blip_if_needed()
    inputs = _blip_processor(images=pil_image, return_tensors="pt")
    import torch
    with torch.no_grad():
        out = _blip_model.generate(**inputs, max_new_tokens=30)
    text = _blip_processor.decode(out[0], skip_special_tokens=True)
    return text

# Send text to judge model
def _send_to_judge(text: str) -> str:
    payload = {
        "model": VLLM_MODEL,
        "messages": [
            {
                "role": "user",
                "content": f"{text}"
            }
        ],
        "max_tokens": 256,
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {VLLM_API_KEY}", "Content-Type": "application/json"}

    with httpx.Client(base_url=VLLM_BASE_URL, timeout=60) as client:
        resp = client.post("/chat/completions", json=payload, headers=headers)
    if resp.status_code != 200:
        logger.error(f"Judge API error: {resp.status_code} - {resp.text}")
        return "Error: Unable to get response from judge model"

    data_resp = resp.json()
    description = (
        data_resp.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "No response")
    )
    return description

@csrf_exempt
def describe_image(request):
    if request.method != "POST":
        return JsonResponse({"error": "Use POST"}, status=405)

    image_file = request.FILES.get("image")
    prompt = request.POST.get("prompt", "").strip()

    b64_image = None
    blip_caption = None

    # Generate BLIP caption if image is provided
    if image_file:
        try:
            image = Image.open(image_file).convert("RGB")
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            b64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

            blip_caption = _caption_with_blip(image)
        except Exception as e:
            return JsonResponse({"error": f"Invalid image: {str(e)}"}, status=400)

    # Build final text to send
    final_text = ""
    if prompt and blip_caption:
        final_text = f"{prompt}\n\nImage description (from BLIP): {blip_caption}"
    elif prompt:
        final_text = prompt
    elif blip_caption:
        final_text = blip_caption
    else:
        return JsonResponse({"error": "Missing prompt or image"}, status=400)

    # Send to judge only if there is text to analyze
    judge_response = _send_to_judge(final_text) if final_text else None

    return JsonResponse({
        "description": judge_response,
        "blip_caption": blip_caption,
        "prompt": prompt,
        "image": f"data:image/jpeg;base64,{b64_image}" if b64_image else None,
        "description_source": "judge" if judge_response else "blip"
    })

def ui(request):
    return render(request, "caption/ui.html")

def _load_sd_if_needed():
    global _sd_loaded, _sd_pipeline
    if _sd_loaded:
        return
    with _blip_lock:  # Reuse lock
        if _sd_loaded:
            return
        from diffusers import StableDiffusionPipeline
        import torch
        _sd_pipeline = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
        )
        _sd_pipeline = _sd_pipeline.to("cpu")
        _sd_loaded = True

def _generate_image_with_sd(prompt: str) -> Image.Image:
    _load_sd_if_needed()
    import torch
    with torch.no_grad():
        result = _sd_pipeline(
            prompt,
            num_inference_steps=20,  # Fewer steps for faster CPU generation
            guidance_scale=7.5,
            width=512,
            height=512,
        )
    return result.images[0]

@csrf_exempt
def generate_image(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST with 'prompt' field"}, status=405)

    data = request.json if hasattr(request, 'json') else {}
    if not data:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    prompt = data.get("prompt", "").strip()
    if not prompt:
        return JsonResponse({"error": "Missing prompt"}, status=400)

    try:
        image = _generate_image_with_sd(prompt)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        b64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return JsonResponse({
            "image": f"data:image/png;base64,{b64_image}",
            "prompt": prompt,
            "source": "stable-diffusion"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)