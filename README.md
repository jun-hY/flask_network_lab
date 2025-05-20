# Interactive Network Security Lab

An interactive web-based platform for network security labs with real-time terminal access to Docker containers.

## Features

- Web-based terminal interface using xterm.js
- Real-time interaction with Docker containers
- Support for multiple concurrent users
- Responsive design that works on desktop and mobile
- Secure WebSocket communication

## Prerequisites

- Docker
- Python 3.8+
- Node.js and npm (for xterm.js addons)
- Linux or WSL2 (Windows Subsystem for Linux 2)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd flask_network_lab
   ```

2. Make the run script executable:
   ```bash
   chmod +x run.sh
   ```

3. Run the setup script:
   ```bash
   ./run.sh
   ```

   This will:
   - Install Python dependencies
   - Pull the required Docker image
   - Install xterm.js addons
   - Start the application

4. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

1. Select a lab from the main page
2. Click "실습 시작" to start the lab environment
3. Use the terminal to interact with the container
4. Click "실습 종료" to stop the lab environment

## Project Structure

- `app.py`: Main application entry point
- `run_terminal.py`: Script to run the application with terminal support
- `controllers/`: Request handlers and WebSocket event handlers
- `templates/`: HTML templates
- `static/`: Static files (CSS, JavaScript, images)
- `Docker/`: Docker Compose files and volume scripts
- `terminal_utils.py`: Terminal process management utilities

## Development

To run the development server:

```bash
python3 run_terminal.py
```

The application will be available at `http://localhost:5000`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [xterm.js](https://xtermjs.org/) - Terminal front-end component
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/) - WebSocket support for Flask
- [Python-on-whales](https://github.com/gabrieldemarmiesse/python-on-whales) - Docker SDK for Python
