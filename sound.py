import pygame

sounds = {}
channels = {}

def load_sounds():
    global sounds, channels
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.mixer.init()
    
    sound_files = {
        'engine': 'assets/sounds/engine.wav',
        'wind': 'assets/sounds/wind.wav',
        'ground': 'assets/sounds/ground.wav',
        'shoot': 'assets/sounds/shoot.wav',
        'crash': 'assets/sounds/crash.wav',
        'splash': 'assets/sounds/splash.wav',
        'stall': 'assets/sounds/stall_warning.wav'
    }

    for name, path in sound_files.items():
        try:
            sounds[name] = pygame.mixer.Sound(path)
        except (pygame.error, FileNotFoundError) as e:
            print(f"Warning: Could not load sound '{name}' from {path}. Error: {e}")
            sounds[name] = None

    # Reserve channels for looping sounds
    channels['engine'] = pygame.mixer.Channel(0) if sounds.get('engine') else None
    channels['wind'] = pygame.mixer.Channel(1) if sounds.get('wind') else None
    channels['ground'] = pygame.mixer.Channel(2) if sounds.get('ground') else None

def play_engine(volume=0.15):
    if channels.get('engine') and sounds.get('engine'):
        channels['engine'].play(sounds['engine'], loops=-1)
        channels['engine'].set_volume(volume)

def stop_engine():
    if channels.get('engine'):
        channels['engine'].stop()

def set_engine_volume(volume):
    if channels.get('engine'):
        volume = max(0.0, min(0.3, volume))
        channels['engine'].set_volume(volume)

def play_wind(volume=1.0):
    if channels.get('wind') and sounds.get('wind'):
        channels['wind'].play(sounds['wind'], loops=-1)
        channels['wind'].set_volume(volume)

def stop_wind():
    if channels.get('wind'):
        channels['wind'].stop()

def set_wind_volume(volume):
    if channels.get('wind'):
        volume = max(0.0, min(1.0, volume))
        channels['wind'].set_volume(volume)

def play_ground(volume=1.0):
    if channels.get('ground') and sounds.get('ground'):
        channels['ground'].play(sounds['ground'], loops=-1)
        channels['ground'].set_volume(volume)

def stop_ground():
    if channels.get('ground'):
        channels['ground'].stop()

def set_ground_volume(volume):
    if channels.get('ground'):
        volume = max(0.0, min(1.0, volume))
        channels['ground'].set_volume(volume)

def play_crash():
    if sounds.get('crash'):
        sounds['crash'].play()

def stop_all_looping():
    stop_engine()
    stop_wind()
    stop_ground()

def stop_all_sounds():
    pygame.mixer.stop()

def play_stall_warning():
    if sounds.get('stall'):
        sounds['stall'].play()

def play_shoot():
    if sounds.get('shoot'):
        sounds['shoot'].play()

def play_splash(volume=0.8):
    if sounds.get('splash'):
        sounds['splash'].set_volume(volume)
        sounds['splash'].play() 