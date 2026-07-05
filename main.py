"""Entry point for the image quality analyzer app."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.app.main import main  # noqa: E402

import flet as ft

if __name__ == "__main__":
    # Support running in browser mode to bypass desktop client registration issues
    view = ft.AppView.WEB_BROWSER if "--web" in sys.argv else ft.AppView.FLET_APP
    ft.app(target=main, view=view)

