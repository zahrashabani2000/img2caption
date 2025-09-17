from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import io
import base64
import httpx
import os
import threading

_blip_lock = threading.Lock()
_blip_loaded = False
_blip_processor = None
_blip_model = None


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


VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "http://127.0.0.1:8000/v1")
VLLM_API_KEY = os.environ.get("VLLM_API_KEY", "EMPTY")


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
            text = data["choices"][0]["message"]["content"]
            return JsonResponse({"description": text, "source": "vllm"})
        # Fall back to BLIP on non-200 from vLLM
        caption = _caption_with_blip(image)
        return JsonResponse({"description": caption, "source": "blip"})
    except Exception:
        # Fall back to BLIP on connection/other errors
        try:
            caption = _caption_with_blip(image)
            return JsonResponse({"description": caption, "source": "blip"})
        except Exception as e2:
            return JsonResponse({"error": str(e2)}, status=500)


def ui(request):
    return render(request, "caption/ui.html")

# Create your views here.
