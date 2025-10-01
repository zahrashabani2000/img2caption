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
        conversation_history = request.session.get('conversation_history', [])

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

        # Build request payload to Rhino Light API with conversation history
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

        # Add the new user message to conversation history
        user_message = {
            "role": "user",
            "content": content_parts,
        }
        conversation_history.append(user_message)

        # Prepare messages for API call - include conversation history
        messages = conversation_history.copy()

        # Add a system message to let AI know this is a continuing conversation
        if len(conversation_history) > 1:
            system_message = {
                "role": "system",
                "content": "This is a continuing conversation. Previous messages are provided for context. The user is asking you to continue the discussion."
            }
            messages.insert(0, system_message)

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

        # Add AI response to conversation history
        assistant_message = {
            "role": "assistant",
            "content": assistant_text
        }
        conversation_history.append(assistant_message)

        # Save updated conversation history to session
        request.session['conversation_history'] = conversation_history

        return JsonResponse({
            "reply": assistant_text,
            "message": message,
            "image": data_url,
            "source": "rhino-light",
            "conversation_continued": len(conversation_history) > 2  # True if this isn't the first exchange
        })
    except Exception as e:
        logger.error(f"Unexpected error in chat: {e}")
        return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)

@csrf_exempt
def new_chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "Use POST"}, status=405)

    try:
        # Clear conversation history from session
        if 'conversation_history' in request.session:
            del request.session['conversation_history']

        return JsonResponse({"message": "New chat started"})
    except Exception as e:
        logger.error(f"Unexpected error in new_chat: {e}")
        return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)

def ui(request):
    return render(request, "caption/ui.html")
