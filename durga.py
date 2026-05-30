#!/usr/bin/env python3
"""Development server script - clears cache and starts Django dev server."""
import os
import sys
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent

def clear_cache():
    """Clear Python cache files."""
    print("🧹 Clearing cache...")
    for path in BASE_DIR.rglob('__pycache__'):
        shutil.rmtree(path, ignore_errors=True)
    for path in BASE_DIR.rglob('*.pyc'):
        path.unlink(missing_ok=True)
    print("✅ Cache cleared.")

def start_server():
    """Start the Django development server."""
    print("🚀 Starting Django development server...")
    venv_python = BASE_DIR / 'venv' / 'bin' / 'python'
    python_path = str(venv_python) if venv_python.exists() else sys.executable
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    subprocess.run([python_path, 'manage.py', 'runserver'], cwd=BASE_DIR)

if __name__ == '__main__':
    skip_cache = '--no-cache' in sys.argv
    if not skip_cache:
        clear_cache()
    start_server()
