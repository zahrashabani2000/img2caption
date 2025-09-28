# AI Image Processing University Project

A Django web application that provides AI-powered image processing capabilities including image captioning and text-to-image generation. Built for Computer Engineering Bachelor's degree project using vLLM platform and CPU-compatible models.

## 🚀 Quick Docker Setup

Rename `.env.example` to `.env` and provide model server variables.

Run with Docker:
```bash
docker-compose up -d
```
Access at: http://localhost:8000/api/ui

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

### Option 1: Docker Deployment (Recommended)

#### 1. Clone the Repository

```bash
git clone <https://github.com/zahrashabani2000/img2caption.git>
cd img2caption
```

#### 2. Create Environment File

```bash
cp .env.example .env
# Edit .env with your configuration
```

#### 3. Build and Run with Docker

```bash
# Build the Docker image
docker-compose build

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f
```

#### 4. Access the Application

- **Frontend**: `http://localhost:8000/api/ui`
- **API**: `http://localhost:8000/api/describe`

### Option 2: Local Development

#### 1. Clone the Repository

```bash
git clone <https://github.com/zahrashabani2000/img2caption.git>
cd img2caption
```

#### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Run Database Migrations

```bash
python manage.py migrate
```

#### 5. Start the Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

#### 6. Access the Application

Open your browser and go to: `http://localhost:8000/api/ui`

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
curl -X POST -F image=@your_image.jpg http://localhost:8000/api/describe
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
  http://localhost:8000/api/generate
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

To use the vLLM platform, you must configure the vLLM model and related settings in the .env file. Create a .env file in the project root and add the following variables:

```bash
# vLLM Configuration
HUGGING_FACE_HUB_TOKEN=your_hugging_face_token
VLLM_BASE_URL=your_server_ip_or_url
VLLM_API_KEY=your_vllm_api_key
VLLM_MODEL=Qwen/Qwen2-VL-2B-Instruct



```
Replace your_hugging_face_token, your_server_ip_or_url, your_vllm_api_key, your_rhino_server_ip_or_url, your_rhino_api_key, and your_rhino_model with the appropriate values for your setup. The HUGGING_FACE_HUB_TOKEN is required for accessing models from Hugging Face, and VLLM_MODEL specifies the model to use with vLLM (e.g., Qwen/Qwen2-VL-2B-Instruct).

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

## Docker Deployment

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

### Quick Docker Commands

```bash
# Build and start the application
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Rebuild after code changes
docker-compose up --build

# Access container shell
docker-compose exec web bash

# Run Django commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic
```

### Docker Configuration

The application uses the following Docker configuration:

- **Base Image**: Python 3.11-slim
- **Port**: 8000 (mapped to host port 8000)
- **Volume Mounts**: Database and static files for persistence
- **Environment**: Supports .env file for configuration
- **Health Check**: Monitors application availability

### Production Deployment

For production deployment, consider:

1. **Environment Variables**: Set `DEBUG=False` and configure proper `SECRET_KEY`
2. **Static Files**: Use a reverse proxy (nginx) to serve static files
3. **Database**: Use PostgreSQL or MySQL instead of SQLite
4. **Security**: Configure proper `ALLOWED_HOSTS` and use HTTPS

### Troubleshooting Docker

```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs web

# Restart the service
docker-compose restart web

# Clean up (removes containers, networks, volumes)
docker-compose down -v

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

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
curl -X POST -F image=@test_image.jpg http://localhost:8000/api/describe
curl -X POST -H "Content-Type: application/json" -d '{"prompt":"test"}' http://localhost:8000/api/generate

# Test with Docker
docker-compose exec web python manage.py test
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
