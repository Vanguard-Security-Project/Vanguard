from datetime import datetime, timezone


def build_report(run_id, filename, graph, persist, analysis, fix, before, after, reanalysis):
    verified = sum(1 for a in after if a.get("verdict") == "verified_fixed")
    still = sum(1 for a in after if a.get("verdict") == "still_vulnerable")

    return {
        "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "filename": filename,
            "nodes": len(graph["nodes"]),
            "edges": len(graph["edges"]),
            "persist": persist,
        },
        "pipeline": ["scan", "analyze", "fix", "re-attack", "verify"],
        "analysis": {
            "node_count": analysis["node_count"],
            "edge_count": analysis["edge_count"],
            "privileged_target_count": analysis["privileged_target_count"],
            "start_count": analysis["start_count"],
            "path_count": analysis["path_count"],
            "high_count": analysis["high_count"],
            "review_count": analysis["review_count"],
            "findings": analysis["findings"],
        },
        "fix": {
            "action_count": fix["plan"]["action_count"],
            "apply_script": fix["plan"]["apply_script"],
            "rollback_script": fix["plan"]["rollback_script"],
            "decisions": [
                {
                    "start": d["finding"].get("start_name"),
                    "target": d["finding"].get("target_name"),
                    "chosen": d["chosen"]["id"] if d.get("chosen") else None,
                    "kind": d["chosen"]["kind"] if d.get("chosen") else None,
                    "blast_radius": d["chosen"]["blast_radius"] if d.get("chosen") else None,
                    "rationale": d.get("rationale"),
                }
                for d in fix["decisions"]
            ],
        },
        "reattack_before": before,
        "verify_after": after,
        "verification_summary": {
            "findings_tested": len(after),
            "verified_fixed": verified,
            "still_vulnerable": still,
        },
        "reanalysis": {
            "path_count": reanalysis["path_count"],
            "high_count": reanalysis["high_count"],
        },
        "notes": [
            "Findings are derived only from the uploaded export.",
            "Graph verification confirms the path exists in the modeled graph.",
            "If real credentials were supplied, Impacket output is in evidence.jsonl.",
            "No AD changes are made by this app - PowerShell is generated for review.",
        ],
    }
