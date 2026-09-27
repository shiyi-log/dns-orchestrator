import os
import sys
from pathlib import Path


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(["manage.py", "runserver", "127.0.0.1:8000", *sys.argv[1:]])
