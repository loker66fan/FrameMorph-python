from __future__ import annotations

from enum import Enum
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from qfluentwidgets import ConfigItem, EnumSerializer, OptionsConfigItem, OptionsValidator, QConfig, Theme, qconfig, setTheme


class FontSizePreset(Enum):
    SMALL = "small"
    STANDARD = "standard"
    LARGE = "large"


APP_SETTINGS_FILE = Path("config/app_settings.json")
DEFAULT_OUTPUT_DIRECTORY = Path.cwd() / "output" / "document_workbench"
FONT_SIZE_POINTS = {
    FontSizePreset.SMALL: 12,
    FontSizePreset.STANDARD: 14,
    FontSizePreset.LARGE: 16,
}
FONT_SIZE_LABELS = {
    FontSizePreset.SMALL: "小",
    FontSizePreset.STANDARD: "标准",
    FontSizePreset.LARGE: "大",
}
THEME_LABELS = {
    Theme.LIGHT: "浅色",
    Theme.DARK: "深色",
}
SUPPORTED_THEMES = (Theme.LIGHT, Theme.DARK)
SUPPORTED_FONT_SIZE_PRESETS = tuple(FONT_SIZE_LABELS)


class AppConfig(QConfig):
    defaultOutputDirectory = ConfigItem("App", "DefaultOutputDirectory", str(DEFAULT_OUTPUT_DIRECTORY))
    fontSizePreset = OptionsConfigItem(
        "App",
        "FontSizePreset",
        FontSizePreset.STANDARD,
        OptionsValidator(FontSizePreset),
        EnumSerializer(FontSizePreset),
    )


app_config = AppConfig()
_settings_loaded = False


def load_app_settings() -> None:
    global _settings_loaded
    if _settings_loaded:
        return
    qconfig.load(APP_SETTINGS_FILE, app_config)
    _settings_loaded = True


def _normalize_directory_path(path: str | Path) -> Path:
    return Path(path).expanduser().absolute()


def get_default_output_directory_path() -> Path:
    load_app_settings()
    value = qconfig.get(app_config.defaultOutputDirectory)
    if not isinstance(value, str) or not value.strip():
        return _normalize_directory_path(DEFAULT_OUTPUT_DIRECTORY)
    return _normalize_directory_path(value)


def set_default_output_directory(path: str | Path, *, save: bool = True) -> Path:
    load_app_settings()
    normalized = _normalize_directory_path(path)
    qconfig.set(app_config.defaultOutputDirectory, str(normalized), save=save)
    return normalized


def ensure_default_output_directory() -> Path:
    output_dir = get_default_output_directory_path()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_font_size_preset() -> FontSizePreset:
    load_app_settings()
    value = qconfig.get(app_config.fontSizePreset)
    if isinstance(value, FontSizePreset):
        return value
    return FontSizePreset.STANDARD


def set_font_size_preset(preset: FontSizePreset, *, save: bool = True) -> None:
    load_app_settings()
    qconfig.set(app_config.fontSizePreset, preset, save=save)
    apply_app_font_size()


def get_supported_theme(theme: Theme) -> Theme:
    return theme if theme in SUPPORTED_THEMES else Theme.LIGHT


def get_current_theme() -> Theme:
    load_app_settings()
    theme = qconfig.get(app_config.themeMode)
    if isinstance(theme, Theme):
        return get_supported_theme(theme)
    return Theme.LIGHT


def apply_app_theme() -> Theme:
    theme = get_current_theme()
    setTheme(theme, save=False)
    return theme


def apply_app_font_size(app: QApplication | None = None) -> None:
    load_app_settings()
    application = app or QApplication.instance()
    if application is None:
        return

    preset = get_font_size_preset()
    font = QFont(application.font())
    font.setPointSize(FONT_SIZE_POINTS[preset])
    application.setFont(font)


def apply_app_appearance(app: QApplication | None = None) -> None:
    load_app_settings()
    apply_app_theme()
    apply_app_font_size(app)
