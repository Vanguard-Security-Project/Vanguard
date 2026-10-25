import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from backend.db import Base


def _now():
    return datetime.now(timezone.utc)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True)
    status = Column(String(32), default="new")
    stage = Column(String(32), default="scan")
    source_name = Column(String(512), default="")

    created_at = Column(DateTime(timezone=True), default=_now)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    analysis_json = Column(Text, default="{}")
    decisions_json = Column(Text, default="[]")
    plan_json = Column(Text, default="{}")
    verification_json = Column(Text, default="{}")
    reanalysis_json = Column(Text, default="{}")
    persist_json = Column(Text, default="{}")


def dumps(obj):
    return json.dumps(obj, separators=(",", ":"), default=str)


def loads(text):
    return json.loads(text) if text else None
