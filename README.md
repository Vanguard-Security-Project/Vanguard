# Vanguard

Defensive Active Directory attack-path pipeline.

SCAN → ANALYZE → FIX → RE-ATTACK → VERIFY

Takes a SharpHound or BloodHound export, finds every path from a normal
user to a Tier-0 target, proposes the least-disruptive fix for each one,
and verifies the fix by re-running the check after applying it.

## What it is not

- It doesn't connect to AD. It writes PowerShell for a human to review.
- It doesn't generate test data. Give it nothing, it does nothing.
- It doesn't claim safety when it finds nothing. An empty result means
  "no paths in this export", not "the environment is clean".

## Quick start

With Docker:

    cp .env.example .env
    docker compose up --build -d
    # open http://localhost:8000, upload an export

Without Docker:

    pip install -r requirements.txt
    python cli.py pipeline path/to/sharp-bundle.zip

## Tests

    python run_tests.py -v

Runs offline. Uses inline fixtures, no external services.

## Files

| Path | Purpose |
|------|---------|
| `collection/` | Parse exports into the graph shape |
| `analysis/` | Enumerate paths, score them, pick fixes |
| `remediation/` | Write PowerShell apply/rollback scripts |
| `validation/` | Verify before/after; optional real re-attack |
| `backend/` | FastAPI + dashboard |
| `lab/` | Optional Windows AD lab build script |
| `cli.py` | Same pipeline, no Docker |
| `tests/` | Unit tests |

## Safety boundaries

- Backend never modifies AD.
- Real re-attack requires credentials you supply explicitly.
- Every verification is logged to `/data/evidence/evidence.jsonl`.
- Every generated PowerShell is written to `/data/scripts/` and never
  executed by the service.

## Limitations

- RBCD trustees aren't decoded from the raw SD blob yet.
- GPOApply edges aren't emitted, only GPLink.
- Graph verification proves the modeled path is gone. Validate with a
  fresh collection after applying a fix for real.
- Real re-attack needs Impacket or NetExec installed on the host.
