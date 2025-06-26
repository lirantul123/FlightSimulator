# Multiplayer Flight Simulator

**Description: What makes this sim unique?**

**Multiplayer Flight Simulator** is a fast, modern, and accessible dogfighting sim inspired by classic web games, but rebuilt from scratch in Python with a focus on smooth multiplayer, intuitive controls, and instant fun. Unlike most flight sims, it's easy to pick up, runs on almost any computer, and lets you jump straight into action with friends.

### Key Features
- **Seamless Multiplayer:** Host or join dogfights with friends or players worldwide.
- **Multiple Plane Types:** Choose from unique aircraft, each with distinct speed, altitude, and firepower.
- **Realistic-yet-Accessible Flight Model:** Enjoy physics that feel authentic but are easy to learn.
- **Damage, Fuel, and Stalls:** Manage your plane's health, fuel, and avoid stalls for survival.
- **Full 3D Graphics:** Modern OpenGL rendering with dynamic environments, weather, and day/night cycles.
- **Scoreboard & Combat Sync:** Real-time tracking of kills, deaths, and scores across all players.
- **Minimap & HUD:** Stay aware of enemies and your own status with a clear, modern interface.
- **No Bots, No Filler:** 100% real players—focus is on pure multiplayer action.
- **Cross-platform:** Works on Windows, Mac, and Linux.

### Controls
- **W/S:** Throttle up/down
- **A/D:** Turn left/right (on ground)
- **Arrow Keys:** Pitch and roll (in air)
- **SPACE:** Fire guns
- **C:** Cycle camera views
- **T:** Open chat
- **ESC:** Pause/Resume

A simple, fun, multiplayer flight simulator built with Python, PyOpenGL, and Pygame. Inspired by fly.pieter.com, this project features:
- A modern, polished UI
- Multiplayer dogfights
- Multiple plane types with unique stats

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

---
Built with blood, sweat and tears.