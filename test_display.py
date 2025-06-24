import pygame
import sys

def test_display():
    pygame.init()
    
    # Try different display modes
    modes_to_try = [
        (800, 600),
        (1024, 768),
        (1200, 800)
    ]
    
    for width, height in modes_to_try:
        try:
            print(f"Trying resolution: {width}x{height}")
            screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption(f"Test Window {width}x{height}")
            
            # Fill with a bright color to make it obvious
            screen.fill((255, 0, 0))  # Bright red
            pygame.display.flip()
            
            print(f"Success! Window should be visible at {width}x{height}")
            print("Press any key to continue...")
            
            # Wait for user input
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        waiting = False
                        break
            
            return True
            
        except Exception as e:
            print(f"Failed with {width}x{height}: {e}")
            continue
    
    print("All display modes failed!")
    return False

if __name__ == "__main__":
    test_display() 