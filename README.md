# AI Image Processing University Project

A Django web application that provides AI-powered image processing capabilities including image captioning and conversational AI with vision. Built for Computer Engineering Bachelor's degree project using Rhino Light API (vLLM-based).

## 🚀 Quick Docker Setup

Rename `.env.example` to `.env` and provide model server variables.

Run with Docker:
```bash
docker-compose up -d
```
Access at: http://localhost:8000/api/ui

## Features

- **Image Captioning**: Upload an image and get an AI-generated description using Rhino vision model
- **Conversational AI with Vision**: Chat with images using natural language with full conversation history support
- **Chat Continuity**: Maintain conversation context across multiple messages - AI remembers previous exchanges
- **Session Management**: Start new conversations or continue existing ones with persistent chat history
- **Web Interface**: Modern, interactive UI with real-time chat status and conversation controls
- **API Endpoints**: RESTful API for programmatic access with session-based conversation management

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

2. **Conversational Chat with Images**:
   - Click on "Chat" tab
   - Upload an image and/or enter a message to start a conversation
   - **Continue the conversation**: Send follow-up messages - the AI remembers the entire conversation history
   - **Conversation status**: See real-time indicators showing if you're continuing a conversation
   - **Start fresh**: Click the "New Chat" button to clear conversation history and begin a new discussion
   - Ask questions, request analysis, or discuss multiple aspects of the image - context is maintained across all messages

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
  "source": "rhino-light",
  "conversation_continued": false
}
```

#### Start New Chat Session
```bash
curl -X POST http://localhost:8000/api/new_chat
```

Response:
```json
{
  "message": "New chat started"
}
```

This endpoint clears the conversation history and allows you to start a fresh conversation.

### Conversation History Management

The application maintains conversation context using Django's session framework:

- **Session Storage**: Conversation history is stored server-side and linked to each user's browser session
- **Message Persistence**: All user messages and AI responses are saved and sent to the AI for context
- **Context Awareness**: The AI receives full conversation history with each request, enabling coherent multi-turn conversations
- **Session Isolation**: Each user has their own separate conversation history
- **Memory Management**: Conversations persist across page refreshes but can be cleared with the "New Chat" button

**Technical Details**:
- Messages are stored in OpenAI-compatible format with `role` and `content` fields
- First message starts a new conversation; subsequent messages include full history
- System messages are automatically added to inform the AI about conversation continuity

## Architecture

### Models Used

1. **Vision and Chat (Rhino Light API)**:
   - Primary: Rhino vision model via vLLM OpenAI-compatible API
   - Supports both image captioning and conversational AI with vision
   - Hosted at: `https://rhino-light-api.ssl.qom.ac.ir`

### Project Structure

```
Image_processing_uni_project/
├── caption/                 # Django app
│   ├── views.py            # API endpoints (chat, new_chat)
│   ├── urls.py             # URL routing with session management
│   └── ...
├── visionapp/              # Django project settings
│   ├── settings.py         # Session configuration
│   ├── urls.py             # Main URL configuration
│   └── ...
├── templates/              # HTML templates
│   └── caption/
│       └── ui.html         # Interactive chat interface with conversation controls
├── requirements.txt        # Python dependencies
├── manage.py              # Django management
└── README.md              # This file
```

### Key Components for Chat Functionality

- **Session Management**: Django sessions store conversation history per user
- **Message History**: Persistent storage of user/AI message pairs
- **Context Preservation**: Full conversation context sent to AI with each request
- **UI State Management**: Real-time conversation status indicators
- **New Chat Handler**: Session cleanup and conversation reset functionality

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
4. **Chat enhancements**: Extend conversation management in session handling
5. **Session features**: Add conversation export, save/load functionality, or multi-user chat rooms

### Testing

```bash
# Run Django tests
python manage.py test

# Test chat API endpoints
curl -X POST -F image=@test_image.jpg -F message="What do you see?" http://localhost:8000/api/chat

# Test conversation continuity (send follow-up messages)
curl -X POST -H "Content-Type: application/json" \
  -d '{"message": "Can you describe the colors in more detail?"}' \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  http://localhost:8000/api/chat

# Test new chat functionality
curl -X POST http://localhost:8000/api/new_chat

# Test with Docker
docker-compose exec web python manage.py test
```

**Chat Testing Tips**:
- Use browser developer tools to inspect session cookies
- Test conversation persistence across multiple requests
- Verify `conversation_continued` field in API responses
- Test "New Chat" button clears conversation history

## License

This project is created for educational purposes as part of a Computer Engineering Bachelor's degree program.

## Contributing

This is a university project. For questions or issues, please contact the project author.

## Acknowledgments

- Django framework and session management
- Rhino Light API (Qom University)
- vLLM platform for vision-language models
- OpenAI API specification for chat completions
- Conversation history and context management implementation
