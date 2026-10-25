# Run it

## 1. Collect from a domain you own

On a domain-joined Windows host:

    Import-Module .\SharpHound.ps1
    Invoke-BloodHound -CollectionMethod All -OutputDirectory .\out -OutputPrefix vanguard
    Compress-Archive .\out\* vanguard-bundle.zip

That ZIP is a full map of your directory. Handle it like a password dump.

## 2. Start the service

    docker compose up --build -d
    until curl -sf http://localhost:8000/api/health >/dev/null; do sleep 2; done

## 3. Upload

Open http://localhost:8000. Choose `vanguard-bundle.zip`. Click Run.

You'll see:
- Stage 1: node and edge counts, Neo4j persist status
- Stage 2: every path to Tier-0, scored
- Stage 3+4: least-disruptive fix per path, blast radius shown
- Stage 4: confirmation each path existed before
- Stage 5: confirmation each path is gone after
- Re-analysis: paths remaining

Two files are written for you to review:
- `/data/scripts/Apply-Fix.ps1`
- `/data/scripts/Rollback-Fix.ps1`

## 4. Apply for real (optional)

Only after change approval:

    .\Apply-Fix.ps1 -WhatIf
    .\Apply-Fix.ps1

## CLI, no Docker

    pip install -r requirements.txt
    python cli.py pipeline vanguard-bundle.zip

Writes `plans/Apply-Fix.ps1` and `vanguard-report.json`.

## If something's wrong

- "export contains no recognizable nodes" — ZIP didn't have the expected
  JSON files. Check with `unzip -l vanguard-bundle.zip`.
- "Neo4j unavailable" — pipeline still runs on memory. Check
  `docker compose logs neo4j`.
- Zero findings — collection may have been scoped too narrowly. Re-collect
  with `-CollectionMethod All`.
