# IPTV Re-Streaming Manager Backend

This is the backend API for the IPTV Re-Streaming Manager system. It handles stream management, authentication, and process control for the IPTV re-streaming application.

## Features

- RESTful API for stream management
- User authentication with JWT
- Stream process management (ffmpeg)
- Stream status monitoring and logging
- Database integration with PostgreSQL

## Technology Stack

- Python 3.9+
- FastAPI
- SQLAlchemy
- PostgreSQL
- ffmpeg for stream processing

## Development

### Prerequisites

- Python 3.9+
- PostgreSQL
- ffmpeg

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the development server:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

### Authentication
- `POST /auth/register`: Register a new user
- `POST /auth/login`: Login and get JWT token
- `GET /auth/me`: Get current user information

### Streams
- `GET /streams`: List all streams
- `POST /streams`: Create a new stream
- `GET /streams/{id}`: Get stream details
- `PUT /streams/{id}`: Update stream
- `DELETE /streams/{id}`: Delete stream
- `POST /streams/{id}/start`: Start stream
- `POST /streams/{id}/stop`: Stop stream
- `POST /streams/{id}/restart`: Restart stream
- `GET /streams/{id}/logs`: Get stream logs
- `GET /streams/{id}/status`: Get stream status

## Docker

The application is containerized using Docker and can be run as part of the complete IPTV Re-Streaming Manager system using Docker Compose.

## Configuration

The application uses environment variables for configuration:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Secret key for JWT encoding
- `RTMP_SERVER`: RTMP server URL
- `HLS_SERVER`: HLS server URL

## License

This project is licensed under the MIT License.
