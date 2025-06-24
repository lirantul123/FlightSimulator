import pygame

sounds = {}
channels = {}

def load_sounds():
    global sounds, channels
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.mixer.init()
    
    sound_files = {
        'engine': 'sounds/engine.wav',
        'wind': 'sounds/wind.wav',
        'shoot': 'sounds/shoot.wav',
        'stall': 'sounds/stall_warning.mp3'
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

def play_stall_warning():
    print("Attempting to play stall warning sound...")
    if sounds.get('stall'):
        sounds['stall'].play()
    else:
        print("Stall sound not loaded!")

def play_shoot():
    if sounds.get('shoot'):
        sounds['shoot'].play()

def stop_all_looping():
    stop_engine()
    stop_wind()

def stop_all_sounds():
    pygame.mixer.stop() 