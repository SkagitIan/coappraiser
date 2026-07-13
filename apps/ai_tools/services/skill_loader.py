from pathlib import Path
import yaml
from django.conf import settings

REQUIRED = {"name", "slug", "description", "status"}

def load_skills():
    skills = []
    for path in (Path(settings.BASE_DIR) / "skills").glob("*/SKILL.md"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        _, front, body = text.split("---", 2)
        meta = yaml.safe_load(front) or {}
        if REQUIRED.issubset(meta) and meta.get("status") == "active":
            skills.append({"path": str(path), "instructions": body.strip(), **meta})
    return skills

def load_skill(slug):
    for skill in load_skills():
        if skill["slug"] == slug:
            return skill
    raise ValueError(f"Unknown or inactive skill: {slug}")

