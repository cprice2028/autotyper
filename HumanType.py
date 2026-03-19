#!/usr/bin/env python3
"""
humantype.py — Types text for you with realistic speed and typos.
Wayland-native via ydotool (recommended) or xdotool fallback.

Setup:
    sudo pacman -S ydotool          # Wayland-native (recommended for Niri)
    sudo systemctl enable --now ydotool
    sudo usermod -aG input $USER    # log out and back in after this

    OR for X11/XWayland only:
    sudo pacman -S xdotool

Usage:
    python3 humantype.py
    python3 humantype.py --wpm 80 --error-rate 0.05
    python3 humantype.py --wpm 60 --error-rate 0.02 --text "Hello world"
"""

import argparse
import random
import shutil
import subprocess
import time
import sys

# ── Backend detection ────────────────────────────────────────────────────────

def detect_backend() -> str:
    if shutil.which('ydotool'):
        return 'ydotool'
    if shutil.which('xdotool'):
        return 'xdotool'
    print("Error: no typing backend found.")
    print("Install one of:")
    print("  sudo pacman -S ydotool   # Wayland-native (recommended)")
    print("  sudo pacman -S xdotool   # X11/XWayland only")
    sys.exit(1)

BACKEND = detect_backend()

def send_char(ch: str) -> None:
    """Send a single character via the active backend."""
    if BACKEND == 'ydotool':
        subprocess.run(['ydotool', 'type', '--', ch],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(['xdotool', 'type', '--clearmodifiers', '--', ch],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def send_backspace() -> None:
    if BACKEND == 'ydotool':
        subprocess.run(['ydotool', 'key', '14:1', '14:0'],   # keycode 14 = BackSpace
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(['xdotool', 'key', 'BackSpace'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ── QWERTY adjacency map ─────────────────────────────────────────────────────

ADJACENCY: dict[str, str] = {
    'a': 'sqwz', 'b': 'vghn', 'c': 'xdfv', 'd': 'serfcx', 'e': 'wrsdf',
    'f': 'drtgvc', 'g': 'ftyhbv', 'h': 'gyujnb', 'i': 'uojk', 'j': 'huiknb',
    'k': 'jiol',  'l': 'kop',   'm': 'njk',   'n': 'bhjm',  'o': 'iklp',
    'p': 'ol',    'q': 'wa',    'r': 'edft',  's': 'awedxz','t': 'rfgy',
    'u': 'yhji',  'v': 'cfgb',  'w': 'qase',  'x': 'zsdc',  'y': 'tghu',
    'z': 'asx',
    '1': '2q', '2': '13wq', '3': '24ew', '4': '35re', '5': '46tr',
    '6': '57yt', '7': '68uy', '8': '79ui', '9': '80io', '0': '9p',
}

def adjacent_char(ch: str) -> str:
    neighbors = ADJACENCY.get(ch.lower(), '')
    if not neighbors:
        return ch
    typo = random.choice(neighbors)
    return typo.upper() if ch.isupper() else typo

# ── Core typing logic ────────────────────────────────────────────────────────

def wpm_to_delay(wpm: int) -> float:
    return 60.0 / (wpm * 5)

def type_text(text: str, wpm: int, error_rate: float, countdown: int = 3) -> None:
    base_delay = wpm_to_delay(wpm)

    print(f"\n▶  Typing {len(text)} chars at ~{wpm} WPM  |  {error_rate*100:.1f}% error rate  |  backend: {BACKEND}")
    print(f"   Starting in ", end='', flush=True)
    for i in range(countdown, 0, -1):
        print(f"{i}...", end=' ', flush=True)
        time.sleep(1)
    print("Go!\n")

    i = 0
    while i < len(text):
        ch = text[i]

        # ── Typo injection ───────────────────────────────────────────────────
        if ch.isalpha() and random.random() < error_rate:
            typo_type = random.choice(['adjacent', 'double', 'swap'])

            if typo_type == 'adjacent':
                send_char(adjacent_char(ch))
                time.sleep(base_delay * random.uniform(0.8, 1.4))
                send_backspace()
                time.sleep(base_delay * random.uniform(0.9, 1.8))

            elif typo_type == 'double' and i + 1 < len(text):
                send_char(ch)
                time.sleep(base_delay * random.uniform(0.5, 0.9))
                send_char(ch)
                time.sleep(base_delay * random.uniform(0.8, 1.5))
                send_backspace()
                time.sleep(base_delay * random.uniform(0.9, 1.6))

            elif typo_type == 'swap' and i + 1 < len(text):
                next_ch = text[i + 1]
                send_char(next_ch)
                time.sleep(base_delay * random.uniform(0.5, 0.9))
                send_char(ch)
                time.sleep(base_delay * random.uniform(1.0, 2.0))
                send_backspace()
                time.sleep(base_delay * 0.4)
                send_backspace()
                time.sleep(base_delay * random.uniform(1.0, 1.8))

        # ── Correct character ────────────────────────────────────────────────
        send_char(ch)

        if ch in ' \n':
            delay = base_delay * random.uniform(0.8, 2.0)
        elif ch in '.,!?;:':
            delay = base_delay * random.uniform(1.2, 2.5)
        else:
            delay = base_delay * random.uniform(0.4, 1.6)

        if random.random() < 0.01:          # occasional thinking pause
            delay += random.uniform(0.3, 1.2)

        time.sleep(delay)
        i += 1

    print("\n✓  Done.")


def get_multiline_input() -> str:
    """Read multiline text from stdin until user types END on its own line."""
    print("Paste or type your text below.")
    print("When done, press Enter then type END on a new line and press Enter:\n")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == 'END':
            break
        lines.append(line)
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Type text at a target WPM with realistic typos.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 humantype.py
  python3 humantype.py --wpm 90 --error-rate 0.04
  python3 humantype.py --wpm 60 --error-rate 0.0 --text "No typos please"
  python3 humantype.py --countdown 5
        """
    )
    parser.add_argument('--wpm', type=int, default=70,
                        help='Typing speed in words per minute (default: 70)')
    parser.add_argument('--error-rate', type=float, default=0.03,
                        help='Fraction of chars that trigger a typo, e.g. 0.05 = 5%% (default: 0.03)')
    parser.add_argument('--text', type=str, default=None,
                        help='Text to type (skips interactive prompt)')
    parser.add_argument('--countdown', type=int, default=3,
                        help='Seconds to count down before typing starts (default: 3)')
    args = parser.parse_args()

    # Validate
    if args.wpm < 1 or args.wpm > 300:
        print("Error: --wpm must be between 1 and 300")
        sys.exit(1)
    if not (0.0 <= args.error_rate <= 1.0):
        print("Error: --error-rate must be between 0.0 and 1.0")
        sys.exit(1)

    # Get text
    if args.text:
        text = args.text
    else:
        text = get_multiline_input()

    if not text.strip():
        print("No text provided. Exiting.")
        sys.exit(0)

    print(f"\n{'─'*50}")
    print(f"  WPM:        {args.wpm}")
    print(f"  Error rate: {args.error_rate*100:.1f}%")
    print(f"  Characters: {len(text)}")
    print(f"{'─'*50}")
    print("  Click where you want to type, then wait for the countdown.")
    print(f"{'─'*50}")

    type_text(text, wpm=args.wpm, error_rate=args.error_rate, countdown=args.countdown)


if __name__ == '__main__':
    main()