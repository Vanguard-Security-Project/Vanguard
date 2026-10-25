import json
import os
from datetime import datetime, timezone
from pathlib import Path

_DIR = Path(os.environ.get("VANGUARD_EVIDENCE_DIR", "./evidence"))
_DIR.mkdir(parents=True, exist_ok=True)
_FILE = _DIR / "evidence.jsonl"


def record(label, finding_id, result):
    entry = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "label": label,
        "finding_id": finding_id,
        "result": result,
    }
    with _FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def list_all():
    if not _FILE.exists():
        return []
    out = []
    for line in _FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def clear():
    if _FILE.exists():
        _FILE.unlink()
