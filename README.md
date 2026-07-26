# DualShock 4 Rumble Control

![Yes](https://github.com/bayeggex/DualShockDriver/raw/main/Videos/Kay%C4%B1t%202026-07-26%20223940.gif)


## Overview

This project lets you control the two internal rumble motors of a Sony DualShock 4 (PS4) controller from a PC using the keyboard, and provides a small command-sequence system for scripting patterns of motor activity.

It does not and cannot make the controller physically move across a surface. A DualShock 4 has no wheels, treads, or locomotion motors of any kind. The only motors inside the controller are two internal rumble (haptic feedback) weights: one low-frequency (strong) motor and one high-frequency (weak) motor. Everything in this project works by turning those two motors on and off in different patterns and intensities to simulate a sense of direction or motion. This is a software and hardware limitation that cannot be worked around with code.

## How It Works

The script uses `pygame`, which wraps the SDL2 library. SDL2 can detect the DualShock 4 as a joystick device and expose its two rumble motors through `Joystick.rumble(low_frequency, high_frequency, duration_ms)`.

- `low_frequency` controls the strong, low-frequency motor (usually on the left side of the controller).
- `high_frequency` controls the weak, high-frequency motor (usually on the right side).
- Both values range from 0.0 (off) to 1.0 (full strength).
- `duration_ms` is how long the motors should run; `0` means run until explicitly stopped with `stop_rumble()`.

On Windows, SDL2 does not enable rumble over Bluetooth by default for the DualShock 4. This is a known SDL limitation, not a bug in this script. To work around it, the script sets three environment variables before `pygame` is imported:

```python
os.environ["SDL_JOYSTICK_HIDAPI"] = "1"
os.environ["SDL_JOYSTICK_HIDAPI_PS4"] = "1"
os.environ["SDL_JOYSTICK_HIDAPI_PS4_RUMBLE"] = "1"
```

These force SDL to use its HIDAPI driver for PS4 controllers and explicitly enable rumble over Bluetooth. Over USB, rumble generally works without this workaround, but the environment variables are harmless to leave in either way.

## Requirements

- Python 3.8 or newer
- `pygame` version 2.1.3 or newer (earlier versions do not reliably support DualShock 4 rumble)
- Windows, with the controller connected either by USB cable or paired over Bluetooth

Install the dependency with:

```bash
pip install --upgrade pygame
```

## File Structure

The project is a single file: `ds4_wasd_rumble.py`. There are no other dependencies or supporting files.

## Running the Script

```bash
python ds4_wasd_rumble.py
```

A small window titled "DS4 Kontrol" will open. This window is required because keyboard input is captured through `pygame`'s event loop, which only receives events while one of its windows has focus. Click on the window to make sure it has focus before pressing keys.

The console will also print the name of the detected controller. If no controller is found, the script prints a message and exits.

## Controls

| Key | Action |
|---|---|
| W | Simulated forward feel: strong motor at full intensity, weak motor at reduced intensity, held down for as long as the key is pressed |
| S | Simulated backward feel: weak motor at full intensity, strong motor at reduced intensity, held down for as long as the key is pressed |
| A | Strong (low-frequency) motor only, held down for as long as the key is pressed |
| D | Weak (high-frequency) motor only, held down for as long as the key is pressed |
| P | Runs the predefined command sequence stored in the `COMMANDS` list |
| ESC | Closes the window and exits the program |

For W, A, S, and D, the motors start when the key is pressed down and stop the instant the key is released. There is no ramping or easing; the transition is immediate.

## Command Sequence System

The `COMMANDS` list near the top of the file lets you script a sequence of motor actions that will run automatically and in order when you press P. This is the infrastructure for defining something like "turn right four times, then move forward for two seconds."

```python
COMMANDS = [
    ("right", 4),
    ("forward", 2.0),
    ("left", 2),
    ("backward", 1.0),
]
```

Each entry is a tuple of `(action, value)`. Four actions are supported:

- `("right", n)`: pulses the weak (right) motor `n` times. Each pulse is 150 milliseconds on and 150 milliseconds off.
- `("left", n)`: pulses the strong (left) motor `n` times, using the same timing as `right`.
- `("forward", seconds)`: holds both motors on continuously for the given number of seconds, weighted the same way as the W key (strong motor dominant).
- `("backward", seconds)`: holds both motors on continuously for the given number of seconds, weighted the same way as the S key (weak motor dominant).

To change what P does, edit the `COMMANDS` list directly in the file and rerun the script. The list is read once, when `main()` starts, so changes require a restart to take effect.

The sequence runs in a separate background thread (`execute_commands` spawns a `threading.Thread`), so the window stays responsive and you can still close it or press other keys while a sequence is playing. Because `pulse` and `hold` use `time.sleep`, the sequence executes at real-world timing: `("right", 4)` takes 4 x 300ms = 1.2 seconds, `("forward", 2.0)` takes 2 seconds, and so on, added up in order.

## Extending the Command System

If you want more actions beyond forward, backward, left, and right, add a new branch inside `execute_commands`:

```python
elif action == "your_action":
    your_function(js, ...)
```

Any new action needs to eventually call `set_rumble` and `stop_rumble` (directly or through helpers like `pulse` and `hold`) since those are the only two functions that actually talk to the controller hardware.

## Function Reference

- `find_ds4()`: Scans all connected joysticks and returns the first one whose name matches "wireless controller", "ps4", or "dualshock" (case-insensitive). If none match, it falls back to joystick index 0. Returns `None` if no joystick is connected at all.
- `set_rumble(js, low, high, duration_ms)`: Starts the rumble motors at the given intensities. Wrapped in a try/except because some drivers raise a `pygame.error` if rumble is unsupported; in that case the call silently does nothing rather than crashing the program.
- `stop_rumble(js)`: Immediately stops both motors.
- `pulse(js, low, high, count, on_ms, off_ms)`: Turns the motors on and off `count` times in a row, blocking the calling thread until finished.
- `hold(js, low, high, seconds)`: Turns the motors on at the given intensities for a fixed duration, blocking the calling thread until finished.
- `execute_commands(js, commands)`: Runs a list of `(action, value)` tuples against `pulse` and `hold` in a background thread.
- `main()`: Initializes `pygame` and the joystick subsystem, opens the window, and runs the event loop that reads keyboard input and dispatches to the functions above.

## Known Limitations

- No physical movement. This project only controls vibration intensity and timing. It cannot make the controller drive, roll, or relocate itself in any way.
- Bluetooth rumble depends on SDL's HIDAPI driver working correctly with your specific Bluetooth adapter and Windows Bluetooth stack. If rumble still does not work after the environment variable workaround, try removing and re-pairing the controller in Windows Bluetooth settings, or test over USB to confirm the hardware itself is functional.
- Only one controller is used at a time. If multiple controllers are connected, `find_ds4()` picks the first one matching a DualShock 4 name pattern.
- The window must have keyboard focus for input to register, since `pygame` reads keyboard events through its own window, not globally.

## Troubleshooting
Confirm `pygame` is updated to 2.1.3 or later. Confirm the environment variables are set before `import pygame` runs (they must be set before `pygame` is imported anywhere, including implicitly). Try USB first to isolate whether the issue is Bluetooth-specific.

**No controller detected**
Make sure the controller is paired and shows as connected in Windows Bluetooth settings, or that the USB cable is a data cable (not charge-only). Re-run the script after confirming the connection.

**Window does not respond to key presses**
Click on the "DS4 Kontrol" window to give it focus. Keyboard input is only captured while this window is active.
