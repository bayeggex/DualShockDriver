import os

os.environ["SDL_JOYSTICK_HIDAPI"] = "1"
os.environ["SDL_JOYSTICK_HIDAPI_PS4"] = "1"
os.environ["SDL_JOYSTICK_HIDAPI_PS4_RUMBLE"] = "1"

import sys
import time
import threading
import pygame

LOW = 0.8
HIGH = 0.8


## Custom command sequence: (action, value) pairs
COMMANDS = [
    ("right", 4),
    ("forward", 2.0),
    ("left", 2),
    ("backward", 1.0),
]
## :)


def find_ds4():
    if pygame.joystick.get_count() == 0:
        return None
    for i in range(pygame.joystick.get_count()):
        js = pygame.joystick.Joystick(i)
        js.init()
        name = js.get_name().lower()
        if "wireless controller" in name or "ps4" in name or "dualshock" in name:
            return js
    js = pygame.joystick.Joystick(0)
    js.init()
    return js


def set_rumble(js, low, high, duration_ms=0):
    try:
        js.rumble(low, high, duration_ms)
    except pygame.error:
        pass


def stop_rumble(js):
    try:
        js.stop_rumble()
    except pygame.error:
        pass


def pulse(js, low, high, count, on_ms=150, off_ms=150):
    for _ in range(count):
        set_rumble(js, low, high, on_ms)
        time.sleep(on_ms / 1000)
        time.sleep(off_ms / 1000)
    stop_rumble(js)


def hold(js, low, high, seconds):
    set_rumble(js, low, high, int(seconds * 1000))
    time.sleep(seconds)
    stop_rumble(js)


def execute_commands(js, commands):
    def worker():
        for action, value in commands:
            if action == "right":
                pulse(js, 0.0, HIGH, int(value))
            elif action == "left":
                pulse(js, LOW, 0.0, int(value))
            elif action == "forward":
                hold(js, LOW, HIGH * 0.3, float(value))
            elif action == "backward":
                hold(js, LOW * 0.3, HIGH, float(value))
    threading.Thread(target=worker, daemon=True).start()


def main():
    pygame.init()
    pygame.joystick.init()

    js = find_ds4()
    if js is None:
        print("Controller Not Found.")
        sys.exit(1)

    print(f"Device: {js.get_name()}")
    print("W:Forward S:Backward A:Left D:Right P:Command Sequence ESC:Exit")

    screen = pygame.display.set_mode((420, 200))
    pygame.display.set_caption("DS4 Control")
    font = pygame.font.SysFont(None, 28)

    active_key = None
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_w:
                    active_key = "W"
                    set_rumble(js, LOW, HIGH * 0.3, 0)
                elif event.key == pygame.K_s:
                    active_key = "S"
                    set_rumble(js, LOW * 0.3, HIGH, 0)
                elif event.key == pygame.K_a:
                    active_key = "A"
                    set_rumble(js, LOW, 0.0, 0)
                elif event.key == pygame.K_d:
                    active_key = "D"
                    set_rumble(js, 0.0, HIGH, 0)
                elif event.key == pygame.K_p:
                    active_key = "komut dizisi"
                    execute_commands(js, COMMANDS)

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d):
                    active_key = None
                    stop_rumble(js)

        screen.fill((20, 20, 30))
        text = active_key if active_key else "W/A/S/D/P"
        surf = font.render(text, True, (255, 255, 255))
        screen.blit(surf, (20, 80))
        pygame.display.flip()
        clock.tick(60)

    stop_rumble(js)
    pygame.quit()


if __name__ == "__main__":
    main()