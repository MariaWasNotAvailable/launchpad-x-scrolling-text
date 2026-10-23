#!/usr/bin/env python3
"""Scroll text across a Launchpad X using its built-in SysEx text-scroll command.

Usage:
    python launchpad_scroll.py [TEXT] [SPEED] [OPTIONS]

Arguments:
    TEXT    Text to scroll (default: "Hello world!")
    SPEED   Scroll speed in pads/second, integer 1-63 (default: 6, medium).
            Values >= 64 scroll right-to-left.

Options:
    -c, --color COLOR  Text color. One of:
                       * "R G B" — three 8-bit RGB integers 0-255 (default: 0 127 0 -> green)
                       * "#RRGGBB" — hexadecimal HTML color (case insensitive, e.g. #00ff00)
                       * a named HTML color (e.g. green, crimson, goldenrod)
    -l, --loop          Loop the scroll continuously (default: scroll once).
    --stop              Send an empty scroll message to stop any ongoing scroll, then exit.

The Launchpad X handles the scrolling and LED color internally, so this
script sends one SysEx message and exits; the text keeps scrolling on the
device until you send an empty scroll message (use --stop) or power-cycle it.

Requires: pip install mido python-rtmidi
"""

import argparse
import sys

import mido

# Launchpad X text-scroll SysEx header (Host -> Device).
# F0 00 20 29 02 0C 07 <payload...> F7
# 0C = scroll across pads + right-side buttons.
HEADER = [0x00, 0x20, 0x29, 0x02, 0x0C, 0x07]

DEFAULT_TEXT = "Hello world!"
DEFAULT_SPEED = 6          # pads/second -> medium
MAX_SPEED = 63             # left-to-right; >=64 reverses direction

# Default text color (R, G, B), each 0-127.
DEFAULT_COLOR = (0, 127, 0)  # green

# 140 named HTML / CSS colors (name -> (R, G, B)).
HTML_NAMED_COLORS = {
    "aliceblue": (240, 248, 255),
    "antiquewhite": (250, 230, 210),
    "aqua": (0, 255, 255),
    "aquamarine": (127, 255, 212),
    "azure": (240, 255, 255),
    "beige": (245, 245, 220),
    "bisque": (255, 228, 196),
    "black": (0, 0, 0),
    "blanchedalmond": (255, 235, 205),
    "blue": (0, 0, 255),
    "blueviolet": (138, 43, 226),
    "brown": (165, 42, 42),
    "burlywood": (222, 184, 135),
    "cadetblue": (95, 158, 160),
    "chartreuse": (127, 255, 0),
    "chocolate": (210, 105, 30),
    "coral": (255, 127, 80),
    "cornflowerblue": (100, 149, 237),
    "cornsilk": (255, 248, 220),
    "crimson": (220, 20, 60),
    "cyan": (0, 255, 255),
    "darkblue": (0, 0, 139),
    "darkcyan": (0, 139, 139),
    "darkgoldenrod": (184, 134, 11),
    "darkgray": (169, 169, 169),
    "darkgreen": (0, 100, 0),
    "darkkhaki": (189, 183, 107),
    "darkmagenta": (139, 0, 139),
    "darkolivegreen": (85, 107, 47),
    "darkorange": (255, 140, 0),
    "darkorchid": (153, 50, 204),
    "darkred": (139, 0, 0),
    "darksalmon": (233, 150, 122),
    "darkseagreen": (143, 188, 143),
    "darkslateblue": (72, 61, 139),
    "darkslategray": (47, 79, 79),
    "darkturquoise": (0, 206, 209),
    "darkviolet": (148, 0, 211),
    "deeppink": (255, 20, 147),
    "deepskyblue": (0, 191, 255),
    "dimgray": (105, 105, 105),
    "dodgerblue": (30, 144, 255),
    "firebrick": (178, 34, 34),
    "floralwhite": (255, 250, 240),
    "forestgreen": (34, 139, 34),
    "fuchsia": (255, 0, 255),
    "gainsboro": (220, 220, 220),
    "ghostwhite": (248, 248, 255),
    "gold": (255, 215, 0),
    "goldenrod": (218, 165, 32),
    "gray": (128, 128, 128),
    "green": (0, 128, 0),
    "greenyellow": (173, 255, 47),
    "honeydew": (240, 255, 240),
    "hotpink": (255, 105, 180),
    "indianred": (205, 92, 92),
    "indigo": (75, 0, 130),
    "ivory": (255, 255, 240),
    "khaki": (240, 230, 140),
    "lavender": (230, 230, 250),
    "lavenderblush": (255, 240, 245),
    "lawngreen": (124, 252, 0),
    "lemonchiffon": (255, 250, 205),
    "lightblue": (173, 216, 230),
    "lightcoral": (240, 128, 128),
    "lightcyan": (224, 255, 255),
    "lightgoldenrodyellow": (250, 250, 210),
    "lightgray": (211, 211, 211),
    "lightgreen": (144, 238, 144),
    "lightpink": (255, 182, 193),
    "lightsalmon": (255, 160, 122),
    "lightseagreen": (32, 178, 170),
    "lightskyblue": (135, 206, 250),
    "lightslategray": (119, 136, 153),
    "lightslategrey": (119, 136, 153),
    "lightsteelblue": (176, 196, 222),
    "lightyellow": (255, 255, 224),
    "lime": (0, 255, 0),
    "limegreen": (50, 205, 50),
    "linen": (250, 240, 230),
    "magenta": (255, 0, 255),
    "maroon": (128, 0, 0),
    "mediumaquamarine": (102, 205, 170),
    "mediumblue": (0, 0, 205),
    "mediumorchid": (186, 85, 211),
    "mediumpurple": (147, 112, 219),
    "mediumseagreen": (60, 179, 113),
    "mediumslateblue": (123, 104, 238),
    "mediumspringgreen": (0, 250, 154),
    "mediumturquoise": (72, 209, 204),
    "mediumvioletred": (199, 21, 133),
    "midnightblue": (25, 25, 112),
    "mintcream": (245, 255, 250),
    "mistyrose": (255, 228, 225),
    "moccasin": (255, 228, 181),
    "navajowhite": (255, 222, 173),
    "navy": (0, 0, 128),
    "oldlace": (253, 245, 230),
    "olive": (128, 128, 0),
    "olivedrab": (107, 142, 35),
    "orange": (255, 165, 0),
    "orangered": (255, 69, 0),
    "orchid": (218, 112, 214),
    "palegoldenrod": (238, 232, 170),
    "palegreen": (152, 251, 152),
    "paleturquoise": (175, 238, 238),
    "palevioletred": (219, 112, 146),
    "papayawhip": (255, 239, 213),
    "peachpuff": (255, 218, 185),
    "peru": (205, 133, 63),
    "pink": (255, 192, 203),
    "plum": (221, 160, 221),
    "powderblue": (176, 224, 230),
    "purple": (128, 0, 128),
    "rebeccapurple": (102, 51, 153),
    "red": (255, 0, 0),
    "rosybrown": (188, 143, 143),
    "royalblue": (65, 105, 225),
    "saddlebrown": (139, 69, 19),
    "salmon": (250, 128, 114),
    "sandybrown": (244, 164, 96),
    "seagreen": (46, 139, 87),
    "seashell": (255, 245, 238),
    "sienna": (160, 82, 45),
    "silver": (192, 192, 192),
    "skyblue": (135, 206, 235),
    "slateblue": (106, 90, 205),
    "slategray": (112, 128, 144),
    "slategrey": (112, 128, 144),
    "snow": (255, 250, 250),
    "springgreen": (0, 255, 127),
    "steelblue": (70, 130, 180),
    "tan": (210, 180, 140),
    "teal": (0, 128, 128),
    "thistle": (216, 191, 216),
    "tomato": (255, 99, 71),
    "turquoise": (64, 224, 208),
    "violet": (238, 130, 238),
    "wheat": (245, 222, 179),
    "white": (255, 255, 255),
    "yellow": (255, 255, 0),
}


def clamp_8bit(value):
    return max(0, min(255, int(value)))


def clamp_7bit(value):
    return max(0, min(127, int(value)))


def parse_hex(value):
    """Parse a #RRGGBB HTML hex color (case insensitive) to an (R, G, B) tuple."""
    hexdigits = value.lstrip("#")
    if len(hexdigits) != 6:
        raise ValueError(f"Invalid hex color '{value}': expected #RRGGBB")
    try:
        return tuple(int(hexdigits[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        raise ValueError(f"Invalid hex color '{value}': expected #RRGGBB")


def parse_named(value):
    """Parse a named HTML color (case insensitive) to an (R, G, B) tuple."""
    key = value.lower()
    if key not in HTML_NAMED_COLORS:
        raise ValueError(f"Unknown named color '{value}'")
    return HTML_NAMED_COLORS[key]


def parse_single_color(value):
    """Parse a single color token: hex #RRGGBB or a named HTML color."""
    value = value.strip()
    if value.startswith("#"):
        return parse_hex(value)
    return parse_named(value)


def build_message(text, speed, color, loop=0):
    speed = clamp_7bit(speed)
    if speed == 0:
        speed = 1
    speed = min(speed, MAX_SPEED)

    # Convert 8-bit RGB (0-255) to 7-bit MIDI (0-127).
    r, g, b = (clamp_7bit(c // 2) for c in color)

    # colorspec: 01 R G B  -> full RGB (4 bytes)
    colorspec = [0x01, r, g, b]

    payload = [int(loop), speed] + colorspec + [ord(c) for c in text]
    return HEADER + payload


def find_launchpad_output():
    for name in mido.get_output_names():
        if "lpx" in name.lower():
            return name
        elif "launchpad" in name.lower():
            print(f"Found Launchpad output '{name}', but it may not be a Launchpad X. Trying it anyway.")
            return name
    return None


def send_stop(port_name):
    stop = mido.Message("sysex", data=HEADER)
    with mido.open_output(port_name) as port:
        port.send(stop)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Scroll text across a Launchpad X via SysEx."
    )
    parser.add_argument("text", nargs="?", default=DEFAULT_TEXT, help="Text to scroll")
    parser.add_argument("speed", nargs="?", type=int, default=DEFAULT_SPEED,
                        help="Scroll speed in pads/second (1-63, default 6)")
    parser.add_argument("-c", "--color", nargs="*", metavar="COLOR",
                        default=None,
                        help="Text color: 'R G B' (8-bit RGB 0-255), '#RRGGBB' hex, "
                             "or a named HTML color (default: 0 127 0 -> green)")
    parser.add_argument("-l", "--loop", action="store_true",
                        help="Loop the scroll continuously (default: scroll once)")
    parser.add_argument("--stop", action="store_true",
                        help="Stop any ongoing scroll on the device, then exit")

    args = parser.parse_args(argv)

    port_name = find_launchpad_output()
    if port_name is None:
        print("No Launchpad MIDI output port found.")
        print("Available outputs:", mido.get_output_names())
        return 1

    if args.stop:
        try:
            send_stop(port_name)
            print("Sent stop message; any ongoing scroll should have ended.")
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to send stop to '{port_name}': {exc}")
            return 1
        return 0

    # Resolve color.
    if args.color is None:
        color = list(DEFAULT_COLOR)
    elif len(args.color) == 1:
        try:
            color = list(parse_single_color(args.color[0]))
        except ValueError as exc:
            parser.error(str(exc))
    elif len(args.color) == 3:
        try:
            color = [clamp_8bit(int(c)) for c in args.color]
        except ValueError:
            parser.error("--color R G B requires three integers 0-255")
    else:
        parser.error("--color expects 'R G B' or a single '#RRGGBB' / named color")

    msg_bytes = build_message(args.text, args.speed, tuple(color), loop=args.loop)
    sysex = mido.Message("sysex", data=msg_bytes)

    try:
        with mido.open_output(port_name) as port:
            port.send(sysex)
        direction = "right-to-left" if args.speed >= 64 else "left-to-right"
        print(f"Sent scroll: {args.text!r} at {args.speed} pads/sec ({direction}).")
        print(f"color: RGB({color[0]}, {color[1]}, {color[2]}), loop={'on' if args.loop else 'off'}.")
        print("The Launchpad X will keep scrolling it on-device.")
        if args.loop:
            print("Use '--stop' to end a looping scroll.")
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to send to '{port_name}': {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
