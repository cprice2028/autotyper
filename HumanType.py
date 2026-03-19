#!/usr/bin/env python3
"""
setup
    sudo pacman -S ydotool           Wayland-native (recommended for Niri)
    sudo systemctl enable --now ydotool
    sudo usermod -aG input $USER    log out and back in after this

    for X11/XWayland only:
    sudo pacman -S xdotool

how to use
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
    error_cooldown = 0

    # Burst state
    burst_speed = 1.0        # current speed multiplier (1.0 = exact wpm)
    burst_remaining = 0      # chars left in this burst

    while i < len(text):
        ch = text[i]

        if burst_remaining <= 0: #newburst
            # multiplier between ~0.75x and ~1.25x, gaussian centered at 1.0
            burst_speed = max(0.6, min(1.5, random.gauss(1.0, 0.12)))
            burst_remaining = random.randint(8, 20)

        burst_remaining -= 1

        # ── Typo injection ───────────────────────────────────────────────────
        if ch.isalpha() and error_cooldown == 0 and random.random() < error_rate:
            typo_type = random.choice(['adjacent', 'swap'])
            min_delay = max(base_delay, 0.05)

            if typo_type == 'adjacent':
                send_char(adjacent_char(ch))
                time.sleep(min_delay * burst_speed * random.uniform(0.8, 1.4))
                send_backspace()
                time.sleep(min_delay * burst_speed * random.uniform(0.9, 1.8))
                error_cooldown = random.randint(3, 8)

            elif typo_type == 'swap' and i + 1 < len(text):
                next_ch = text[i + 1]
                send_char(next_ch)
                time.sleep(min_delay * burst_speed * random.uniform(0.5, 0.9))
                send_char(ch)
                time.sleep(min_delay * burst_speed * random.uniform(1.0, 2.0))
                send_backspace()
                time.sleep(min_delay * burst_speed * 0.4)
                send_backspace()
                time.sleep(min_delay * burst_speed * random.uniform(1.0, 1.8))
                error_cooldown = random.randint(3, 8)
        elif error_cooldown > 0:
            error_cooldown -= 1
        send_char(ch)

        if ch in ' \n':
            delay = base_delay * burst_speed * random.uniform(0.8, 2.0)
        elif ch in '.,!?;:':
            delay = base_delay * burst_speed * random.uniform(1.2, 2.5)
        else:
            delay = base_delay * burst_speed * random.uniform(0.4, 1.6)

        if random.random() < 0.01:
            delay += random.uniform(0.3, 1.2)

        time.sleep(delay)
        i += 1

    print("\n✓  Done.")


def get_multiline_input() -> str:
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


def prompt_int(msg: str, default: int, lo: int, hi: int) -> int:
    while True:
        raw = input(f"  {msg} [{default}]: ").strip()
        if raw == '':
            return default
        try:
            val = int(raw)
            if lo <= val <= hi:
                return val
            print(f"    x Enter a number between {lo} and {hi}.")
        except ValueError:
            print("    x Please enter a whole number.")

def prompt_float(msg: str, default: float, lo: float, hi: float) -> float:
    while True:
        raw = input(f"  {msg} [{default}]: ").strip()
        if raw == '':
            return default
        try:
            val = float(raw)
            if lo <= val <= hi:
                return val
            print(f"    x Enter a number between {lo} and {hi}.")
        except ValueError:
            print("    x Please enter a number.")

def main():
    print("━" * 50)
    print("  humantype -- human-like autotyper")
    print("━" * 50)

    wpm        = prompt_int  ("WPM (1-300)",          70,  1,   300)
    error_pct  = prompt_float("Error rate % (0-100)", 3.0, 0.0, 100.0)
    error_rate = error_pct / 100.0

    text = get_multiline_input()

    if not text.strip():
        print("No text provided. Exiting.")
        sys.exit(0)

    print(f"\n{'─'*50}")
    print(f"  WPM:        {wpm}")
    print(f"  Error rate: {error_pct:.1f}%")
    print(f"  Characters: {len(text)}")
    print(f"{'─'*50}")
    print("  Click where you want to type, then wait for the countdown.")
    print(f"{'─'*50}")

    type_text(text, wpm=wpm, error_rate=error_rate, countdown=3)

if __name__ == '__main__':
    main()