from datetime import datetime, timezone
from pathlib import Path


def _fill(template, ctx):
    for key, value in ctx.items():
        template = template.replace("{" + key + "}", str(value or ""))
    return template


def generate_plan(decisions, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).isoformat()
    high_risk = [d for d in decisions
                 if d.get("chosen") and d["chosen"]["blast_radius"] == "high"]

    apply_lines = [
        "# Vanguard remediation plan",
        "# generated: " + ts,
        "# review before running. requires change approval.",
    ]
    if high_risk:
        apply_lines += [
            "#",
            "# !! WARNING: this plan includes {} HIGH blast-radius fix(es). !!".format(len(high_risk)),
            "# These change delegation/RBCD settings and can break a legitimate",
            "# service account if applied to the wrong principal. Review every",
            "# line marked HIGH RISK below and confirm the target/principal",
            "# values before running it - do not run this whole script blind.",
        ]
    apply_lines += [
        "$ErrorActionPreference = 'Stop'",
        "",
    ]
    rollback_lines = [
        "# Vanguard rollback plan",
        "# generated: " + ts,
        "$ErrorActionPreference = 'Stop'",
        "",
    ]

    count = 0
    for i, d in enumerate(decisions):
        if not d.get("chosen"):
            continue
        count += 1
        ctx = d.get("context", {})
        chosen = d["chosen"]
        apply_lines.append("# fix {}: {} (blast radius: {})".format(
            i + 1, chosen["id"], chosen["blast_radius"].upper()))
        if chosen["blast_radius"] == "high":
            apply_lines.append("# >> HIGH RISK - confirm target/principal before running this line <<")
        apply_lines.append(_fill(chosen["ps_apply"], ctx))
        apply_lines.append("")
        rollback_lines.append("# rollback {}: {}".format(i + 1, chosen["id"]))
        rollback_lines.append(_fill(chosen["ps_rollback"], ctx))
        rollback_lines.append("")

    apply_path = out / "Apply-Fix.ps1"
    rollback_path = out / "Rollback-Fix.ps1"
    apply_path.write_text("\n".join(apply_lines), encoding="utf-8")
    rollback_path.write_text("\n".join(rollback_lines), encoding="utf-8")

    return {
        "apply_script": str(apply_path),
        "rollback_script": str(rollback_path),
        "action_count": count,
        "high_risk_count": len(high_risk),
    }
