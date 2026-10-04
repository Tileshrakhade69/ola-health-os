"""
OLA Health OS - Configuration Module
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")

SECRET_KEY = os.environ.get("SECRET_KEY", "ola-health-os-command-center-secret-key-2026")
PORT = int(os.environ.get("PORT", 5000))
HOST = "0.0.0.0"
DEBUG = True
