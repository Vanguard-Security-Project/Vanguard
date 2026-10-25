import json
import traceback

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from backend import orchestrator
from backend.db import init_db
from backend.ui import INDEX_HTML
from collection import neo4j_client as neo
from validation import evidence, reattack

app = FastAPI(title="Vanguard", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "pipeline": ["scan", "analyze", "fix", "re-attack", "verify"],
        "neo4j_available": neo.is_available(),
    }


@app.post("/api/pipeline/run")
async def pipeline_run(file: UploadFile = File(...), creds_json: str = Form("")):
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "empty upload")
    if len(raw) > 80 * 1024 * 1024:
        raise HTTPException(413, "upload exceeds 80 MB")

    creds = None
    if creds_json.strip():
        try:
            creds = json.loads(creds_json)
        except Exception as exc:
            raise HTTPException(400, "invalid creds_json: " + str(exc))

    try:
        return orchestrator.run_pipeline(file.filename or "upload.json", raw, creds)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(500, "pipeline failed: " + str(exc))


@app.get("/api/evidence")
def list_evidence():
    return {"evidence": evidence.list_all()}


@app.post("/api/validation/real")
def validation_real(body: dict):
    try:
        technique = body["technique"]
        target = body["target"]
        user = body["user"]
        domain = body["domain"]
        secret = body["secret"]
    except KeyError as exc:
        raise HTTPException(400, "missing field: " + str(exc))

    result = reattack.run_real(technique, target, user, domain, secret)
    evidence.record("real-standalone", technique + ":" + target,
                    reattack.to_dict(result))
    return reattack.to_dict(result)
