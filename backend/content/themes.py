import json
import logging
from pathlib import Path
import re

from django.core.exceptions import ValidationError

MAX_CONFIG_BYTES = 64 * 1024
COLOR_TOKENS = {"paper", "ink", "muted", "rule", "panel", "accent"}


def default_theme_config():
    """Return a fresh copy of the bundled JSON configuration."""
    return json.loads(Path(__file__).with_name("themes.json").read_text(encoding="utf-8"))


def validate_theme_config(value):
    if not isinstance(value, dict) or set(value) != {"version", "default", "themes"}:
        raise ValidationError("Theme JSON must contain version, default, and themes.")
    if type(value["version"]) is not int or value["version"] != 1:
        raise ValidationError("Theme JSON version must be 1.")
    themes = value["themes"]
    if not isinstance(themes, list) or not 1 <= len(themes) <= 20:
        raise ValidationError("Provide between 1 and 20 themes.")
    identifiers = set()
    for theme in themes:
        if not isinstance(theme, dict) or set(theme) != {"id", "name", "light", "dark"}:
            raise ValidationError("Each theme must contain id, name, light, and dark.")
        identifier = theme["id"]
        if not isinstance(identifier, str) or len(identifier) > 32 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier):
            raise ValidationError("Theme IDs must be lowercase words/numbers separated by hyphens, at most 32 characters.")
        if identifier in identifiers:
            raise ValidationError("Theme IDs must be unique.")
        identifiers.add(identifier)
        if not isinstance(theme["name"], str) or not theme["name"].strip() or len(theme["name"]) > 50:
            raise ValidationError("Theme names must contain 1 to 50 characters.")
        for mode in ["light", "dark"]:
            colors = theme[mode]
            if not isinstance(colors, dict) or set(colors) != COLOR_TOKENS:
                raise ValidationError(f"{identifier} {mode} must define paper, ink, muted, rule, panel, and accent.")
            if any(not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color) for color in colors.values()):
                raise ValidationError("Colors must use six-digit hexadecimal notation, such as #f3eee3.")
    if not isinstance(value["default"], str) or value["default"] not in identifiers:
        raise ValidationError("Default must match one of the theme IDs.")
    if len(json.dumps(value).encode("utf-8")) > MAX_CONFIG_BYTES:
        raise ValidationError("Theme JSON must be no larger than 64 KiB.")


def public_theme_config(value):
    try:
        validate_theme_config(value)
        return value
    except ValidationError:
        logging.getLogger(__name__).warning("Invalid stored theme configuration; using bundled defaults.")
        return default_theme_config()
