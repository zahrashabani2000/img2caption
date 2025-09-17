# AI Image Processing University Project

A Django web application that provides AI-powered image processing capabilities including image captioning and text-to-image generation. Built for Computer Engineering Bachelor's degree project using vLLM platform and CPU-compatible models.

## Features

- **Image Captioning**: Upload an image and get an AI-generated description
- **Text-to-Image Generation**: Describe what you want and generate an image
- **CPU-Optimized**: Works on CPU-only systems with fallback models
- **Web Interface**: Simple, modern UI for easy interaction
- **API Endpoints**: RESTful API for programmatic access

## System Requirements

- **OS**: Linux (Ubuntu 24.04 recommended)
- **Python**: 3.12+
- **RAM**: 16GB+ recommended
- **Storage**: 10GB+ free space
- **CPU**: Intel Core i3+ (AVX512 support preferred)

## Quick Start

### 1. Clone the Repository

```bash
git clone <https://github.com/zahrashabani2000/img2caption.git>
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run Database Migrations

```bash
python manage.py migrate
```

### 5. Start the Development Server

```bash
python manage.py runserver 0.0.0.0:9000
```

### 6. Access the Application

Open your browser and go to: `http://localhost:9000/api/ui`

## Usage

### Web Interface

1. **Image Captioning**:
   - Click on "Image Caption" tab
   - Upload an image file
   - Click "Generate Caption"
   - View the AI-generated description

2. **Image Generation**:
   - Click on "Generate Image" tab
   - Enter a text description (e.g., "A beautiful sunset over mountains")
   - Click "Generate Image"
   - Wait for the AI to create the image

### API Endpoints

#### Image Captioning
```bash
curl -X POST -F image=@your_image.jpg http://localhost:9000/api/describe
```

Response:
```json
{
  "description": "A beautiful landscape with mountains and trees",
  "source": "blip"
}
```

#### Image Generation
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"prompt": "A cat sitting on a windowsill"}' \
  http://localhost:9000/api/generate
```

Response:
```json
{
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "prompt": "A cat sitting on a windowsill",
  "source": "stable-diffusion"
}
```

## Architecture

### Models Used

1. **Image Captioning**:
   - Primary: vLLM with Qwen2-VL-2B-Instruct (if available)
   - Fallback: BLIP (Salesforce/blip-image-captioning-base)

2. **Image Generation**:
   - Stable Diffusion v1.5 (runwayml/stable-diffusion-v1-5)

### Project Structure

```
Image_processing_uni_project/
├── caption/                 # Django app
│   ├── views.py            # API endpoints
│   ├── urls.py             # URL routing
│   └── ...
├── visionapp/              # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── templates/              # HTML templates
│   └── caption/
│       └── ui.html         # Main web interface
├── requirements.txt        # Python dependencies
├── manage.py              # Django management
└── README.md              # This file
```

## Configuration

### Environment Variables

You can customize the application behavior using environment variables:

```bash
# vLLM Configuration (optional)
export VLLM_BASE_URL="http://127.0.0.1:8000/v1"
export VLLM_MODEL="Qwen/Qwen2-VL-2B-Instruct"
export VLLM_API_KEY="EMPTY"

# Django Configuration
export DJANGO_SETTINGS_MODULE="visionapp.settings"
```

### vLLM Server (Optional)

If you want to use vLLM for better performance:

```bash
# Pull vLLM Docker image
docker pull vllm/vllm-openai:latest

# Run vLLM server (CPU mode)
docker run -d --name vllm-openai-cpu \
  -p 8000:8000 \
  -e VLLM_TARGET_DEVICE=cpu \
  -e VLLM_LOGGING_LEVEL=DEBUG \
  vllm/vllm-openai:latest \
  --host 0.0.0.0 --port 8000 --device cpu \
  --enable-vision \
  --model Qwen/Qwen2-VL-2B-Instruct
```

## Troubleshooting

### Common Issues

1. **"Connection refused" error**:
   - The vLLM server is not running or not accessible
   - The app will automatically fall back to BLIP for captioning

2. **Slow image generation**:
   - Image generation on CPU is slower than GPU
   - Consider reducing image size or inference steps in the code

3. **Out of memory errors**:
   - Close other applications to free up RAM
   - The models require significant memory for first-time loading

4. **Model download issues**:
   - Ensure stable internet connection
   - Models are downloaded on first use (~2-4GB total)

### Performance Tips

- First run will be slower due to model downloads
- Keep the server running to avoid reloading models
- Use smaller images for faster processing
- Consider running on a machine with more RAM for better performance

## Development

### Adding New Features

1. **New API endpoints**: Add to `caption/views.py` and `caption/urls.py`
2. **UI changes**: Modify `templates/caption/ui.html`
3. **New models**: Add loading functions in `caption/views.py`

### Testing

```bash
# Run Django tests
python manage.py test

# Test API endpoints
curl -X POST -F image=@test_image.jpg http://localhost:9000/api/describe
curl -X POST -H "Content-Type: application/json" -d '{"prompt":"test"}' http://localhost:9000/api/generate
```

## License

This project is created for educational purposes as part of a Computer Engineering Bachelor's degree program.

## Contributing

This is a university project. For questions or issues, please contact the project author.

## Acknowledgments

- Django framework
- Hugging Face Transformers
- Stable Diffusion
- BLIP model
- vLLM platform
