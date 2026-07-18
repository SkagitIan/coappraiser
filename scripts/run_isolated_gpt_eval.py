"""Run GPT evaluation with deployment credentials but never its database/storage."""

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = f"sqlite:///{(ROOT / 'db.sqlite3').as_posix()}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.management import execute_from_command_line  # noqa: E402


execute_from_command_line(
    [str(ROOT / "manage.py"), "evaluate_gpt56", *sys.argv[1:]]
)
