import re
from pathlib import Path

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_operator
from app.models.operator import Operator

router = APIRouter(prefix="/admin/version", tags=["admin-version"])

def _find_changelog() -> Path:
    """Find CHANGELOG.md in multiple possible locations."""
    candidates = [
        Path("/app/CHANGELOG.md"),  # Docker: mounted volume
        Path(__file__).resolve().parent.parent.parent.parent.parent / "CHANGELOG.md",  # Local dev: ostrov-vezeniya/CHANGELOG.md
        Path.cwd() / "CHANGELOG.md",  # Fallback: current working directory
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]  # Default (will return empty list if not found)


CHANGELOG_PATH = _find_changelog()


def _parse_changelog() -> list[dict]:
    """Parse CHANGELOG.md into structured version entries."""
    if not CHANGELOG_PATH.exists():
        return []

    text = CHANGELOG_PATH.read_text(encoding="utf-8")
    versions: list[dict] = []
    current: dict | None = None

    for line in text.splitlines():
        # Match version header: ## [0.3.0] — 2026-03-10
        m = re.match(r"^## \[(.+?)\]\s*[—–-]\s*(.+)$", line)
        if m:
            if current:
                versions.append(current)
            current = {
                "version": m.group(1),
                "date": m.group(2).strip(),
                "sections": [],
            }
            continue

        if current is None:
            continue

        # Match section header: ### Добавлено
        m = re.match(r"^### (.+)$", line)
        if m:
            current["sections"].append({
                "title": m.group(1).strip(),
                "items": [],
            })
            continue

        # Match list item: - Something
        m = re.match(r"^- (.+)$", line)
        if m and current.get("sections"):
            current["sections"][-1]["items"].append(m.group(1).strip())

    if current:
        versions.append(current)

    return versions


@router.get("")
async def get_version_info(
    operator: Operator = Depends(get_current_operator),
):
    """Return current version and full changelog."""
    from app.main import APP_VERSION

    changelog = _parse_changelog()
    return {
        "current_version": APP_VERSION,
        "changelog": changelog,
    }
