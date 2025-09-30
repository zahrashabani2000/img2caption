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


_sd_loaded = False
_sd_pipeline = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rhino Light API configuration (defaults match provided curl)
RHINO_LIGHT_BASE_URL = os.environ.get("RHINO_LIGHT_BASE_URL", "https://rhino-light-api.ssl.qom.ac.ir")
RHINO_LIGHT_KEY = os.environ.get("RHINO_LIGHT_KEY", "default")
RHINO_LIGHT_MODEL = os.environ.get("RHINO_LIGHT_MODEL", "rhino")
RHINO_MAX_IMAGE_SIDE = int(os.environ.get("RHINO_MAX_IMAGE_SIDE", "1024"))
RHINO_JPEG_QUALITY = int(os.environ.get("RHINO_JPEG_QUALITY", "80"))

def _call_rhino_light(messages: list, temperature: float = 0.8, top_p: float = 0.95, max_tokens: int = 200, model: str = None) -> dict:
    payload = {
        "model": model or RHINO_LIGHT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {RHINO_LIGHT_KEY}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=60) as client:
        resp = client.post(f"{RHINO_LIGHT_BASE_URL}/v1/chat/completions", json=payload, headers=headers)
    return {"status": resp.status_code, "data": (resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"text": resp.text})}

@csrf_exempt
def chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "Use POST"}, status=405)

    try:
        # Support multipart form (message + image)
        message = ""
        image_file = None

        if request.content_type and request.content_type.startswith("multipart/form-data"):
            message = request.POST.get("message", "").strip()
            image_file = request.FILES.get("image")
        else:
            # Also support JSON body: { "message": string, "image_base64": string }
            try:
                data = json.loads(request.body.decode("utf-8")) if request.body else {}
            except Exception:
                data = {}
            message = (data.get("message", "") or "").strip()
            image_base64_json = data.get("image_base64")
            if image_base64_json:
                # Create a pseudo file payload from provided base64
                image_file = None
                image_b64_str = image_base64_json
            else:
                image_b64_str = None

        # Prepare image base64 if file provided
        data_url = None
        if image_file is not None:
            try:
                img = Image.open(image_file).convert("RGB")
                width, height = img.size
                max_side = max(width, height)
                if max_side > RHINO_MAX_IMAGE_SIDE:
                    scale = RHINO_MAX_IMAGE_SIDE / float(max_side)
                    new_size = (int(width * scale), int(height * scale))
                    img = img.resize(new_size, Image.LANCZOS)
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=RHINO_JPEG_QUALITY, optimize=True, progressive=True)
                image_b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
                content_type = "image/jpeg"
                data_url = f"data:{content_type};base64,{image_b64_str}"
            except Exception as e:
                return JsonResponse({"error": f"Invalid image: {str(e)}"}, status=400)
        else:
            content_type = "image/jpeg"

        # If neither message nor image provided, error
        if not message and not image_file and not (locals().get("image_b64_str")):
            return JsonResponse({"error": "Missing message or image"}, status=400)

        # Build request payload to Rhino Light API exactly like provided curl
        content_parts = []
        if message or not locals().get("image_b64_str"):
            content_parts.append({
                "type": "text",
                "text": message or "Describe this image in detail"
            })
        if locals().get("image_b64_str"):
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{content_type};base64,{image_b64_str}"
                }
            })

        messages = [
            {
                "role": "user",
                "content": content_parts,
            }
        ]

        result = _call_rhino_light(messages)

        if result["status"] != 200:
            logger.error(f"Rhino Light API error: {result['status']} - {result.get('data')}")
            return JsonResponse({"error": "Upstream model error"}, status=502)

        data_resp = result["data"]
        assistant_text = (
            data_resp.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "No response")
        )

        return JsonResponse({
            "reply": assistant_text,
            "message": message,
            "image": data_url,
            "source": "rhino-light"
        })
    except Exception as e:
        logger.error(f"Unexpected error in chat: {e}")
        return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)

def ui(request):
    return render(request, "caption/ui.html")
#-------------------------------------------------------------------------------------------------
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