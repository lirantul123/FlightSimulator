# Multiplayer Flight Simulator

A simple, fun, multiplayer flight simulator built with Python, PyOpenGL, and Pygame. Inspired by fly.pieter.com, this project features:
- A modern, polished UI
- Multiplayer dogfights
- Multiple plane types with unique stats
- AI planes for target practice

## How to Run

### 1. Install Dependencies
You'll need Python 3 and the libraries listed in `requirements.txt`. Install them with:
```bash
pip install -r requirements.txt
```

### 2. Start the Server
On the machine that will host the game (or on your local machine for solo play), run the server:
```bash
python3 server.py
```
The server will listen on port 50007. For internet play, you'll need to port-forward this port.

### 3. Run the Game Client
Each player runs the main game:
```bash
python3 main.py
```
- In the settings screen, enter a callsign and the server's IP address.
- Select a plane and click "Start".

## Gameplay Controls
- **W/S**: Throttle
- **A/D**: Turn (on ground)
- **Arrow Keys**: Pitch and Roll (in air)
- **SPACE**: Fire
- **C**: Cycle Camera
- **T**: Open Chat
- **ESC**: Pause/Resume
- **R (while paused)**: Restart game

---
Built with the help of an AI assistant. 