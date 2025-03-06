# IPTV Re-Streaming Manager Frontend

This is the frontend application for the IPTV Re-Streaming Manager system. It provides a user interface for managing and monitoring IPTV streams.

## Features

- User authentication (login/register)
- Dashboard with stream statistics
- Stream management (add, edit, delete, start, stop, restart)
- Stream monitoring with logs and status
- Video preview for active streams

## Technology Stack

- React
- Material UI
- React Router
- Axios for API communication
- Video.js for video playback

## Development

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

1. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

2. Start the development server:
   ```bash
   npm start
   # or
   yarn start
   ```

3. Build for production:
   ```bash
   npm run build
   # or
   yarn build
   ```

## Project Structure

- `src/components/`: Reusable UI components
- `src/contexts/`: React context providers
- `src/pages/`: Application pages
- `src/services/`: API services
- `src/utils/`: Utility functions

## Docker

The application is containerized using Docker. In production, it is served by Nginx.

## Configuration

The application uses environment variables for configuration:

- `REACT_APP_API_URL`: Backend API URL (default: http://localhost:8000)

## License

This project is licensed under the MIT License.
