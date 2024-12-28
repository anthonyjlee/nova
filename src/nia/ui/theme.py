"""Theme and styling for NIA chat interface."""

from gradio.themes.default import Default

def create_theme():
    """Create custom theme for interface."""
    theme = Default()
    theme.font = ("Source Sans Pro", "ui-sans-serif", "system-ui")
    theme.font_mono = ("IBM Plex Mono", "ui-monospace", "monospace")
    return theme
