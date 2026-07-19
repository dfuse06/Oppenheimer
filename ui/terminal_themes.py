"""Built-in xterm.js color themes for the Terminal tab, plus persistence
of the user's chosen theme in output/terminal-settings.json."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_THEME_NAME = "Oppenheimer"

THEMES: dict[str, dict[str, str]] = {
    "Oppenheimer": {
        "background": "#00000000",
        "foreground": "#d8dee9",
        "cursor": "#d6b46c",
        "cursorAccent": "#07080c",
        "selectionBackground": "#6d4b8588",
        "black": "#16171d", "brightBlack": "#5d606d",
        "red": "#df6b75", "brightRed": "#ff7d88",
        "green": "#92c47d", "brightGreen": "#a8dd90",
        "yellow": "#d6b46c", "brightYellow": "#ebca82",
        "blue": "#749bd7", "brightBlue": "#8ab1ed",
        "magenta": "#b78ad1", "brightMagenta": "#cea1e8",
        "cyan": "#72b7bd", "brightCyan": "#87cdd3",
        "white": "#d5d5d8", "brightWhite": "#ffffff",
    },
    "Dracula": {
        "background": "#282a36",
        "foreground": "#f8f8f2",
        "cursor": "#f8f8f2",
        "cursorAccent": "#282a36",
        "selectionBackground": "#44475a99",
        "black": "#21222c", "brightBlack": "#6272a4",
        "red": "#ff5555", "brightRed": "#ff6e6e",
        "green": "#50fa7b", "brightGreen": "#69ff94",
        "yellow": "#f1fa8c", "brightYellow": "#ffffa5",
        "blue": "#bd93f9", "brightBlue": "#d6acff",
        "magenta": "#ff79c6", "brightMagenta": "#ff92df",
        "cyan": "#8be9fd", "brightCyan": "#a4ffff",
        "white": "#f8f8f2", "brightWhite": "#ffffff",
    },
    "Nord": {
        "background": "#2e3440",
        "foreground": "#d8dee9",
        "cursor": "#d8dee9",
        "cursorAccent": "#2e3440",
        "selectionBackground": "#4c566a99",
        "black": "#3b4252", "brightBlack": "#4c566a",
        "red": "#bf616a", "brightRed": "#bf616a",
        "green": "#a3be8c", "brightGreen": "#a3be8c",
        "yellow": "#ebcb8b", "brightYellow": "#ebcb8b",
        "blue": "#81a1c1", "brightBlue": "#88c0d0",
        "magenta": "#b48ead", "brightMagenta": "#b48ead",
        "cyan": "#88c0d0", "brightCyan": "#8fbcbb",
        "white": "#e5e9f0", "brightWhite": "#eceff4",
    },
    "Solarized Dark": {
        "background": "#002b36",
        "foreground": "#839496",
        "cursor": "#93a1a1",
        "cursorAccent": "#002b36",
        "selectionBackground": "#07364599",
        "black": "#073642", "brightBlack": "#586e75",
        "red": "#dc322f", "brightRed": "#cb4b16",
        "green": "#859900", "brightGreen": "#93a1a1",
        "yellow": "#b58900", "brightYellow": "#657b83",
        "blue": "#268bd2", "brightBlue": "#839496",
        "magenta": "#d33682", "brightMagenta": "#6c71c4",
        "cyan": "#2aa198", "brightCyan": "#93a1a1",
        "white": "#eee8d5", "brightWhite": "#fdf6e3",
    },
    "Gruvbox Dark": {
        "background": "#282828",
        "foreground": "#ebdbb2",
        "cursor": "#ebdbb2",
        "cursorAccent": "#282828",
        "selectionBackground": "#50494599",
        "black": "#282828", "brightBlack": "#928374",
        "red": "#cc241d", "brightRed": "#fb4934",
        "green": "#98971a", "brightGreen": "#b8bb26",
        "yellow": "#d79921", "brightYellow": "#fabd2f",
        "blue": "#458588", "brightBlue": "#83a598",
        "magenta": "#b16286", "brightMagenta": "#d3869b",
        "cyan": "#689d6a", "brightCyan": "#8ec07c",
        "white": "#a89984", "brightWhite": "#ebdbb2",
    },
    "One Dark": {
        "background": "#282c34",
        "foreground": "#abb2bf",
        "cursor": "#528bff",
        "cursorAccent": "#282c34",
        "selectionBackground": "#3e445099",
        "black": "#282c34", "brightBlack": "#5c6370",
        "red": "#e06c75", "brightRed": "#e06c75",
        "green": "#98c379", "brightGreen": "#98c379",
        "yellow": "#e5c07b", "brightYellow": "#e5c07b",
        "blue": "#61afef", "brightBlue": "#61afef",
        "magenta": "#c678dd", "brightMagenta": "#c678dd",
        "cyan": "#56b6c2", "brightCyan": "#56b6c2",
        "white": "#abb2bf", "brightWhite": "#ffffff",
    },
    "Monokai": {
        "background": "#272822",
        "foreground": "#f8f8f2",
        "cursor": "#f8f8f0",
        "cursorAccent": "#272822",
        "selectionBackground": "#49483e99",
        "black": "#272822", "brightBlack": "#75715e",
        "red": "#f92672", "brightRed": "#f92672",
        "green": "#a6e22e", "brightGreen": "#a6e22e",
        "yellow": "#f4bf75", "brightYellow": "#f4bf75",
        "blue": "#66d9ef", "brightBlue": "#66d9ef",
        "magenta": "#ae81ff", "brightMagenta": "#ae81ff",
        "cyan": "#a1efe4", "brightCyan": "#a1efe4",
        "white": "#f8f8f2", "brightWhite": "#f9f8f5",
    },
    "Classic Black": {
        "background": "#000000",
        "foreground": "#e6e6e6",
        "cursor": "#e6e6e6",
        "cursorAccent": "#000000",
        "selectionBackground": "#66666699",
        "black": "#000000", "brightBlack": "#666666",
        "red": "#cd3131", "brightRed": "#f14c4c",
        "green": "#0dbc79", "brightGreen": "#23d18b",
        "yellow": "#e5e510", "brightYellow": "#f5f543",
        "blue": "#2472c8", "brightBlue": "#3b8eea",
        "magenta": "#bc3fbc", "brightMagenta": "#d670d6",
        "cyan": "#11a8cd", "brightCyan": "#29b8db",
        "white": "#e5e5e5", "brightWhite": "#ffffff",
    },
}

THEME_NAMES: list[str] = list(THEMES.keys())

_SETTINGS_PATH = Path(__file__).resolve().parent.parent / "output" / "terminal-settings.json"


def get_theme(name: str) -> dict[str, str]:
    return THEMES.get(name, THEMES[DEFAULT_THEME_NAME])


def load_theme_name() -> str:
    try:
        data = json.loads(_SETTINGS_PATH.read_text())
        name = data.get("theme")
        if isinstance(name, str) and name in THEMES:
            return name
    except (OSError, ValueError):
        pass
    return DEFAULT_THEME_NAME


def save_theme_name(name: str) -> None:
    if name not in THEMES:
        return
    try:
        _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _SETTINGS_PATH.write_text(json.dumps({"theme": name}, indent=2))
    except OSError:
        pass
