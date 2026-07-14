"""Bundled font loading for Oppenheimer."""

from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = PROJECT_ROOT / "assets" / "fonts"

DEFAULT_FONT_FAMILY = "Cascadia Code"
DEFAULT_FONT_SIZE = 10


def load_application_fonts() -> str:
    """
    Load every bundled TTF/OTF font and return the preferred font family.

    Falls back to Qt's system fixed-width font if the bundled font cannot
    be loaded.
    """
    loaded_families: list[str] = []

    if FONT_DIR.is_dir():
        font_files = sorted(
            list(FONT_DIR.glob("*.ttf"))
            + list(FONT_DIR.glob("*.otf"))
        )

        for font_file in font_files:
            font_id = QFontDatabase.addApplicationFont(str(font_file))

            if font_id == -1:
                print(f"Warning: could not load bundled font: {font_file}")
                continue

            loaded_families.extend(
                QFontDatabase.applicationFontFamilies(font_id)
            )

    if DEFAULT_FONT_FAMILY in loaded_families:
        return DEFAULT_FONT_FAMILY

    for family in loaded_families:
        if "Cascadia Code" in family:
            return family

    fallback = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    return fallback.family()


def application_font(
    family: str | None = None,
    point_size: int = DEFAULT_FONT_SIZE,
) -> QFont:
    """Create the application's default font."""
    font = QFont(family or DEFAULT_FONT_FAMILY, point_size)
    font.setStyleHint(QFont.StyleHint.Monospace)
    return font
