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
import httpx
import re
import time

# Load environment variables from .env file
load_dotenv()

_blip_lock = threading.Lock()
_blip_loaded = False
_blip_processor = None
_blip_model = None

_sd_loaded = False
_sd_pipeline = None

_judge_lock = threading.Lock()

# Use environment variables only (no defaults)
VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL")
VLLM_API_KEY = os.environ.get("VLLM_API_KEY")
JUDGE_BASE_URL = os.environ.get("JUDGE_BASE_URL")
JUDGE_API_KEY = os.environ.get("JUDGE_API_KEY")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL")


def _load_blip_if_needed():
    global _blip_loaded, _blip_processor, _blip_model
    if _blip_loaded:
        return
    with _blip_lock:
        if _blip_loaded:
            return
        from transformers import BlipProcessor, BlipForConditionalGeneration
        _blip_processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        _blip_model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
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


logger = logging.getLogger(__name__)


def _judge_with_external_api(b64_image: str, description: str, max_retries: int = 3, retry_delay: float = 1.0) -> dict:
    # Check environment variables
    if not JUDGE_BASE_URL or not JUDGE_API_KEY:
        logger.error("Missing JUDGE_BASE_URL or JUDGE_API_KEY environment variables")
        return {
            "score": "Not provided",
            "explanation": "Missing JUDGE_BASE_URL or JUDGE_API_KEY environment variables",
            "source": "none"
        }

    session_payload = {"model": "judge"}
    headers = {"Authorization": f"Bearer {JUDGE_API_KEY}", "Content-Type": "application/json"}

    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(base_url=JUDGE_BASE_URL, timeout=60) as client:
                session_resp = client.post("/judge/chat/Judge.v3/create_session/", json=session_payload,
                                           headers=headers)
                if session_resp.status_code != 200:
                    logger.error(
                        f"Attempt {attempt}: Failed to create session: {session_resp.status_code} - {session_resp.text}")
                    return {
                        "score": "Not provided",
                        "explanation": f"Failed to create session: {session_resp.status_code} - {session_resp.text}",
                        "source": "none"
                    }
                session_id = session_resp.json().get("session_id")
                if not session_id:
                    logger.error(f"Attempt {attempt}: No session_id in API response")
                    return {
                        "score": "Not provided",
                        "explanation": "No session_id provided by API",
                        "source": "none"
                    }
                prompt = f"Judge the quality of this image description on a scale of 1-10, providing a numerical score and a brief explanation: {description}. Image: data:image/jpeg;base64,{b64_image}"
                payload = {"content": prompt}
                resp = client.post(f"/judge/chat/Judge.v3/answer_chat/?session_id={session_id}", json=payload,
                                   headers=headers)
                if resp.status_code != 200:
                    logger.error(f"Attempt {attempt}: Failed to get judgment: {resp.status_code} - {resp.text}")
                    if attempt < max_retries and resp.status_code == 500:
                        time.sleep(retry_delay)
                        continue
                    return {
                        "score": "Not provided",
                        "explanation": f"Failed to get judgment after {attempt} attempts: {resp.status_code} - {resp.text}",
                        "source": "none"
                    }
                content = resp.json().get("content", "No judgment")
                score_match = re.search(r'\b([1-9]|10)\b', content)
                score = int(score_match.group(0)) if score_match else None
                explanation = content if score_match else "No clear score provided in judgment."
                return {
                    "score": score if score is not None else "Not provided",
                    "explanation": explanation,
                    "source": "judge-api"
                }
        except Exception as e:
            logger.error(f"Attempt {attempt}: Error in _judge_with_external_api: {str(e)}")
            if attempt < max_retries:
                time.sleep(retry_delay)
                continue
            return {
                "score": "Not provided",
                "explanation": f"Unable to judge after {max_retries} attempts due to error: {str(e)}",
                "source": "none"
            }

@csrf_exempt
def describe_image(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST an image file under 'image'"}, status=405)

    image_file = request.FILES.get("image")
    if not image_file:
        return JsonResponse({"error": "Missing image file"}, status=400)

    image = Image.open(image_file)
    image = image.convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    b64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Generate description (vLLM primary, BLIP fallback)
    description = None
    source = None
    payload = {
        "model": os.environ.get("VLLM_MODEL", "Qwen/Qwen2-VL-2B-Instruct"),
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image concisely."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                    },
                ],
            }
        ],
        "max_tokens": 128,
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {VLLM_API_KEY}"}
    try:
        with httpx.Client(base_url=VLLM_BASE_URL, timeout=60) as client:
            resp = client.post("/chat/completions", json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            description = data["choices"][0]["message"]["content"]
            source = "vllm"
    except Exception:
        pass

    if not description:
        try:
            description = _caption_with_blip(image)
            source = "blip"
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    # Now judge the description with external API
    # judgment = _judge_with_external_api(b64_image, description)

    return JsonResponse({
        "description": description,
        "description_source": source,
        # **judgment
    })


def ui(request):
    return render(request, "caption/ui.html")


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