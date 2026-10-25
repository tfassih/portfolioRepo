import json

from django import forms
from django.core.validators import FileExtensionValidator

from .models import SiteSettings
from .themes import MAX_CONFIG_BYTES, validate_theme_config


class ThemeJSONWidget(forms.Textarea):
    def format_value(self, value):
        if isinstance(value, str):
            try:
                return json.dumps(json.loads(value), indent=2, ensure_ascii=False)
            except (ValueError, TypeError):
                pass
        return super().format_value(value)


class SettingsForm(forms.ModelForm):
    theme_config = forms.JSONField(
        required=False,
        label="Theme configuration",
        widget=ThemeJSONWidget(attrs={"rows": 24, "cols": 90}),
        help_text="Edit the JSON document, or upload a replacement below. Each theme needs light and dark colors.",
    )
    theme_file = forms.FileField(
        required=False,
        label="Import themes JSON",
        validators=[FileExtensionValidator(["json"])],
        help_text="A UTF-8 .json file, at most 64 KiB. A valid upload replaces the JSON configuration when you save.",
    )

    class Meta:
        model = SiteSettings
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        upload = cleaned.get("theme_file")
        if upload:
            if upload.size > MAX_CONFIG_BYTES:
                self.add_error("theme_file", "Theme JSON must be no larger than 64 KiB.")
                return cleaned
            try:
                config = json.loads(upload.read(MAX_CONFIG_BYTES + 1).decode("utf-8-sig"))
                validate_theme_config(config)
            except (ValueError, UnicodeError, forms.ValidationError) as error:
                self.add_error("theme_file", f"Invalid theme configuration: {error}")
                return cleaned
            cleaned["theme_config"] = config
        elif "theme_config" in cleaned and cleaned["theme_config"] is None:
            self.add_error("theme_config", "Supply a theme configuration or upload a JSON file.")
        return cleaned
