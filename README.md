# Launchpad X Scrolling Text

A Python script that scrolls text across **Launchpad X** using its built-in SysEx text-scroll command.

## Features

* Scrolls arbitrary text across the pads and right-side buttons.
* Configurable scroll **speed** (pads/second).
* Configurable text **color** via 8-bit RGB integers, `#RRGGBB` hex HTML colors, or named HTML colors.
* Scroll **once by default**; loop continuously with `-l` / `--loop`.
* `--stop` sends an empty SysEx message to end any ongoing scroll on the device.
* Sends one SysEx message and exits — the Launchpad X keeps scrolling on-device until stopped.

## Requirements

Python 3 and [`mido`](https://github.com/mido/mido) with a MIDI backend (e.g. `python-rtmidi`):

```bash
pip install mido python-rtmidi
```

## Testing

Unit tests are in `test_launchpad_scroll.py` and can be run with:

```bash
python -m unittest test_launchpad_scroll -v
```

## Usage

```bash
python launchpad_scroll.py [TEXT] [SPEED] [OPTIONS]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `TEXT`   | Text to scroll | `"Hello world!"` |
| `SPEED`  | Scroll speed in pads/second, integer `1–63` (`≥64` reverses direction) | `6` (medium) |

### Options

| Option | Description |
|--------|-------------|
| `-c COLOR`, `--color COLOR` | Text color: `R G B` (8-bit RGB integers `0–255`), `#RRGGBB` hex HTML color (case insensitive), or a named HTML color (e.g. `green`, `crimson`, `goldenrod`; default: `0 127 0` → green) |
| `-l`, `--loop` | Loop the scroll continuously (default: scroll once) |
| `--stop` | Stop any ongoing scroll on the device, then exit |

### Examples

```bash
# Default text, speed, and color; scroll once
python launchpad_scroll.py

# Custom text and speed
python launchpad_scroll.py "Launchpad X" 12

# Custom text, speed, and color (red)
python launchpad_scroll.py "Hello" 8 -c 255 0 0

# Scroll once (default), blue text
python launchpad_scroll.py "Once only" 5 -c 0 0 255

# Hex HTML color (case insensitive)
python launchpad_scroll.py "Neon" 6 -c "#00ff00"
python launchpad_scroll.py "Neon" 6 -c "#FF00FF"

# Named HTML color
python launchpad_scroll.py "Crimson" 6 -c crimson
python launchpad_scroll.py "Gold" 6 -c goldenrod

# Loop continuously (green)
python launchpad_scroll.py "Looping forever" 4 -l

# Loop with custom color
python launchpad_scroll.py "Looping red" 4 -l -c 255 0 0

# Fast right-to-left scroll
python launchpad_scroll.py "Backwards" 70

# Stop any ongoing scroll
python launchpad_scroll.py --stop
```

## Stopping a loop

Because the Launchpad X performs the scrolling on-device, the script exits immediately after sending the SysEx message. If you started a scroll with `-l` / `--loop`, it will keep looping until you either:

1. Run `python launchpad_scroll.py --stop`, or
2. Power-cycle the Launchpad X.

## Supported models

This script targets the **Launchpad X**, using the documented Novation SysEx text-scroll command:

```
F0 00 20 29 02 0C 07 <loop> <speed> <colorspec> <text...> F7
```

* Manufacturer ID `00 20 29` = Novation
* Device ID `02` = Launchpad family
* Command `0C` = text scroll across pads + right-side buttons

**Compatible:** Launchpad X (verified via Novation's Launchpad X documentation).

**Other Launchpad models** (Launchpad Mini, Launchpad MK2, Launchpad Pro, etc.) may use different SysEx headers or may not support text scrolling at all. This script is not guaranteed to work with non-X models without adjusting the `HEADER` and command byte.

## Protocol details

* `<loop>` — `0` = play once, `1` = loop.
* `<speed>` — pads/second (`1–63` left-to-right; `≥64` = right-to-left, formed by `speed − 128`).
* `<colorspec>` — `01 R G B` (full RGB, each `0–127`) or `00 <palette index>`.
* `<text>` — ASCII bytes of the string.

Sending the header with no payload (the `--stop` option) terminates any ongoing scroll.
