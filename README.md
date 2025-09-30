# AI Image Processing University Project

A Django web application that provides AI-powered image processing capabilities including image captioning, text-to-image generation, and conversational AI with vision. Built for Computer Engineering Bachelor's degree project using Rhino Light API (vLLM-based) and CPU-compatible models.

## 🚀 Quick Docker Setup

Rename `.env.example` to `.env` and provide model server variables.

Run with Docker:
```bash
docker-compose up -d
```
Access at: http://localhost:8000/api/ui

## Features

- **Image Captioning**: Upload an image and get an AI-generated description using Rhino vision model
- **Conversational AI with Vision**: Chat with images using natural language
- **Text-to-Image Generation**: Describe what you want and generate an image using Stable Diffusion
- **CPU-Optimized**: Works on CPU-only systems using efficient models
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
- **API**: `http://localhost:8000/api/chat`

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
   - Add an optional prompt or leave blank for default description
   - Click "Generate Caption"
   - View the AI-generated description

2. **Chat with Images**:
   - Click on "Chat" tab
   - Upload an image and/or enter a message
   - Have a conversation about the image with the AI
   - Ask questions or request analysis of the image content

3. **Image Generation**:
   - Click on "Generate Image" tab
   - Enter a text description (e.g., "A beautiful sunset over mountains")
   - Click "Generate Image"
   - Wait for the AI to create the image

### API Endpoints

#### Image Captioning
```bash
curl -X POST -F image=@your_image.jpg -F prompt="Describe this image in detail" http://localhost:8000/api/chat
```

Response:
```json
{
  "description": "A beautiful landscape with mountains and trees under a clear blue sky",
  "prompt": "Describe this image in detail",
  "image": "data:image/jpeg;base64,...",
  "source": "rhino-light"
}
```

#### Chat with Images
```bash
curl -X POST -F image=@your_image.jpg -F message="What colors do you see in this image?" http://localhost:8000/api/chat
```

Or chat without image:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}' \
  http://localhost:8000/api/chat
```

Response:
```json
{
  "reply": "I can see vibrant greens, blues, and earthy browns in this natural landscape scene.",
  "message": "What colors do you see in this image?",
  "image": "data:image/jpeg;base64,...",
  "source": "rhino-light"
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

1. **Vision and Chat (Rhino Light API)**:
   - Primary: Rhino vision model via vLLM OpenAI-compatible API
   - Supports both image captioning and conversational AI with vision
   - Hosted at: `https://rhino-light-api.ssl.qom.ac.ir`

2. **Image Generation**:
   - Stable Diffusion v1.5 (runwayml/stable-diffusion-v1-5)
   - CPU-optimized for local generation

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

Create a `.env` file in the project root and configure the Rhino Light API settings:

```bash
# Rhino Light API Configuration
RHINO_LIGHT_BASE_URL=https://rhino-light-api.ssl.qom.ac.ir
RHINO_LIGHT_TOKEN=default
RHINO_LIGHT_MODEL=rhino

# Image processing settings
RHINO_MAX_IMAGE_SIDE=1024
RHINO_JPEG_QUALITY=80
```

### Available Environment Variables

- `RHINO_LIGHT_BASE_URL`: URL of the Rhino Light API server (default: `https://rhino-light-api.ssl.qom.ac.ir`)
- `RHINO_LIGHT_TOKEN`: API authentication token (default: `default`)
- `RHINO_LIGHT_MODEL`: Model name to use (default: `rhino`)
- `RHINO_MAX_IMAGE_SIDE`: Maximum image dimension for processing (default: `1024`)
- `RHINO_JPEG_QUALITY`: JPEG compression quality for image uploads (default: `80`)

### Rhino Light API

The application uses the Rhino Light API, which is a vLLM-based vision model service hosted at Qom University. This service provides:

- Vision-language understanding
- Image captioning capabilities
- Conversational AI with image context
- OpenAI-compatible API interface

The API is pre-configured and ready to use. No additional server setup is required.

## Troubleshooting

### Common Issues

1. **"Connection refused" or API errors**:
   - Check if the Rhino Light API is accessible
   - Verify your internet connection
   - Ensure RHINO_LIGHT_BASE_URL is correct

2. **Slow image generation**:
   - Image generation on CPU is slower than GPU
   - Consider reducing image size or inference steps in the code

3. **Out of memory errors**:
   - Close other applications to free up RAM
   - Stable Diffusion requires significant memory for image generation

4. **Image upload issues**:
   - Ensure images are under the maximum size limit (RHINO_MAX_IMAGE_SIDE)
   - Supported formats: JPEG, PNG (automatically converted)

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
curl -X POST -F image=@test_image.jpg -F message="What do you see?" http://localhost:8000/api/chat
curl -X POST -H "Content-Type: application/json" -d '{"prompt":"A sunset"}' http://localhost:8000/api/generate

# Test with Docker
docker-compose exec web python manage.py test
```

## License

This project is created for educational purposes as part of a Computer Engineering Bachelor's degree program.

## Contributing

This is a university project. For questions or issues, please contact the project author.

## Acknowledgments

- Django framework
- Rhino Light API (Qom University)
- vLLM platform
- Stable Diffusion
- OpenAI API specification
