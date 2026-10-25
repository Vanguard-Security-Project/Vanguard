import os
from datetime import datetime, timezone
from pathlib import Path

from backend import models
from backend.db import SessionLocal
from backend.reports import build_report

from analysis import decision, scoring
from collection import loader
from collection import neo4j_client as neo
from remediation import actions, planner
from validation import evidence, reattack


SCRIPTS_DIR = Path(os.environ.get("VANGUARD_SCRIPTS_DIR", "./scripts/generated"))
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)


def _persist(graph):
    if not neo.is_available():
        return {"neo4j": "unavailable", "note": "graph kept in memory"}

    neo.ensure_constraints()
    nodes = [{"id": n["id"], "name": n["name"], "kind": n["kind"]}
             for n in graph["nodes"]]
    return {
        "neo4j": "ok",
        "nodes_written": neo.write_nodes(nodes),
        "edges_written": neo.write_edges(graph["edges"]),
    }


def run_pipeline(filename, raw, creds=None):
    graph = loader.load_export(filename, raw)
    if not graph["nodes"]:
        raise ValueError("export contained no nodes")

    persist_info = _persist(graph)

    db = SessionLocal()
    try:
        run = models.PipelineRun(status="running", stage="scan",
                                 source_name=filename)
        db.add(run)
        db.commit()
        db.refresh(run)

        analysis = scoring.analyze_graph(graph, max_hops=8, max_paths=5)

        decisions = decision.decide_batch(analysis["findings"][:10])
        plan = planner.generate_plan(decisions, out_dir=SCRIPTS_DIR)

        fixed = graph
        for d in decisions:
            fixed, _ = actions.apply_to_graph(fixed, d)

        before = []
        for finding in analysis["findings"][:10]:
            gv = reattack.graph_verify(graph, finding, "before")
            evidence.record("before", finding.get("start_id", "?"),
                            reattack.to_dict(gv))
            entry = {"finding": finding, "graph_check": reattack.to_dict(gv)}
            if creds and creds.get("technique"):
                real = reattack.run_real(
                    creds["technique"],
                    creds.get("target") or finding.get("target_name", ""),
                    creds.get("user", ""), creds.get("domain", ""),
                    creds.get("secret", ""),
                )
                evidence.record("before-real", finding.get("start_id", "?"),
                                reattack.to_dict(real))
                entry["real"] = reattack.to_dict(real)
            before.append(entry)

        after = []
        for finding in analysis["findings"][:10]:
            gv = reattack.graph_verify(fixed, finding, "after")
            evidence.record("after", finding.get("start_id", "?"),
                            reattack.to_dict(gv))
            verdict = "verified_fixed" if not gv.succeeded else "still_vulnerable"
            entry = {"finding": finding, "graph_check": reattack.to_dict(gv),
                     "verdict": verdict}
            if creds and creds.get("technique"):
                real = reattack.run_real(
                    creds["technique"],
                    creds.get("target") or finding.get("target_name", ""),
                    creds.get("user", ""), creds.get("domain", ""),
                    creds.get("secret", ""),
                )
                entry["real"] = reattack.to_dict(real)
                if real.succeeded:
                    entry["verdict"] = "still_vulnerable"
            after.append(entry)

        reanalysis = scoring.analyze_graph(fixed, max_hops=8, max_paths=5)

        run.analysis_json = models.dumps(analysis)
        run.decisions_json = models.dumps(decisions)
        run.plan_json = models.dumps(plan)
        run.verification_json = models.dumps({"before": before, "after": after})
        run.reanalysis_json = models.dumps(reanalysis)
        run.persist_json = models.dumps(persist_info)
        run.status = "verified"
        run.stage = "verify"
        run.finished_at = datetime.now(timezone.utc)
        db.commit()

        return build_report(
            run_id=run.id,
            filename=filename,
            graph=graph,
            persist=persist_info,
            analysis=analysis,
            fix={"decisions": decisions, "plan": plan},
            before=before,
            after=after,
            reanalysis=reanalysis,
        )
    finally:
        db.close()
