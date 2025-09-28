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
_blip_pipeline = None


_sd_loaded = False
_sd_pipeline = None

# Environment variables
VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL")
VLLM_API_KEY = os.environ.get("VLLM_API_KEY")
VLLM_MODEL = os.environ.get("VLLM_MODEL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load fast image captioning model
def _load_blip_if_needed():
    global _blip_loaded, _blip_pipeline
    if _blip_loaded:
        return
    with _blip_lock:
        if _blip_loaded:
            return
        try:
            from transformers import pipeline
            import torch

            # Use BLIP with maximum optimizations for speed
            logger.info("Loading optimized BLIP image-to-text pipeline...")
            _blip_pipeline = pipeline(
                "image-to-text",
                model="Salesforce/blip-image-captioning-base",
                device="cpu",
                torch_dtype=torch.float32,
                max_new_tokens=6,  # Very short captions for speed
                min_length=3,  # Minimum length
                num_beams=1,  # Greedy decoding
                do_sample=False,
                use_fast=True,
                model_kwargs={
                    "torch_dtype": torch.float32,
                    "low_cpu_mem_usage": True,
                    "device_map": None
                },
                tokenizer_kwargs={"use_fast": True}
            )
            _blip_loaded = True
            logger.info("Fast image captioning pipeline loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load image captioning pipeline: {e}")
            _blip_loaded = False
            _blip_pipeline = None

def _caption_with_blip(pil_image: Image.Image) -> str:
    _load_blip_if_needed()
    if not _blip_loaded or _blip_pipeline is None:
        return "Error: Model not loaded"

    try:
        # Use the pipeline for fast inference
        result = _blip_pipeline(pil_image)
        caption = result[0]['generated_text'] if result else "No caption generated"
        return caption
    except Exception as e:
        logger.error(f"Error generating caption: {e}")
        return f"Error generating caption: {str(e)}"

def _send_to_rhino(text: str) -> str:
    # Check if VLLM is properly configured
    if not all([VLLM_BASE_URL, VLLM_API_KEY, VLLM_MODEL]):
        logger.warning("VLLM not configured, returning BLIP caption only")
        return None

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

    try:
        with httpx.Client(base_url=VLLM_BASE_URL, timeout=60) as client:  # Reduced timeout from 60 to 30
            resp = client.post("/chat/completions", json=payload, headers=headers)
        if resp.status_code != 200:
            logger.error(f"Rhino API error: {resp.status_code} - {resp.text}")
            return "Error: Unable to get response from rhino model"

        data_resp = resp.json()
        description = (
            data_resp.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "No response")
        )
        return description
    except Exception as e:
        logger.error(f"Error calling VLLM API: {e}")
        return f"Error calling VLLM API: {e}"

@csrf_exempt
def describe_image(request):
    if request.method != "POST":
        return JsonResponse({"error": "Use POST"}, status=405)

    try:
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

        rhino_response = _send_to_rhino(final_text) if final_text else None

        description = rhino_response if rhino_response is not None else blip_caption

        return JsonResponse({
            "description": description,
            "blip_caption": blip_caption,
            "prompt": prompt,
            "image": f"data:image/jpeg;base64,{b64_image}" if b64_image else None,
            "description_source": "rhino" if rhino_response else "blip"
        })
    except Exception as e:
        logger.error(f"Unexpected error in describe_image: {e}")
        return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)

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