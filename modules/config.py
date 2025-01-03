# modules/config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / 'assets'
DATA_DIR = BASE_DIR / 'data'
LOGOS_DIR = ASSETS_DIR / 'logos'

CHROME_OPTIONS = {
    'headless': True,  # Cambiado a False para mostrar la interfaz gráfica
    'disable-gpu': False,  # Cambiado a False para habilitar el procesamiento GPU
    'no-sandbox': True,
    'disable-dev-shm-usage': True
}