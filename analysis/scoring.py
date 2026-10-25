WEIGHTS = {
    "GenericAll":          1.00,
    "GetChangesAll":       1.00,
    "GenericWrite":        0.95,
    "WriteDacl":           0.95,
    "WriteOwner":          0.90,
    "ForceChangePassword": 0.90,
    "GetChanges":          0.90,
    "AllExtendedRights":   0.85,
    "AddMember":           0.85,
    "AllowedToAct":        0.85,
    "RBCD":                0.85,
    "AllowedToDelegate":   0.80,
    "AdminTo":             0.60,
    "GPLink":              0.50,
    "HasSession":          0.40,
    "CanRDP":              0.30,
    "MemberOf":            0.20,
}

TIER0_NAMES = {
    "DOMAIN ADMINS", "ENTERPRISE ADMINS", "SCHEMA ADMINS",
    "ADMINISTRATORS", "DOMAIN CONTROLLERS", "KRBTGT",
    "PROTECTED USERS", "ENTERPRISE KEY ADMINS", "KEY ADMINS",
}


def _length_factor(hops):
    return max(0.30, 1.0 - (hops - 1) * 0.10)


def _tier_factor(target_name):
    return 1.0 if target_name.strip().upper() in TIER0_NAMES else 0.7


def score_finding(finding):
    edges = finding.get("edges", [])
    if not edges:
        finding["score"] = 0.0
        finding["risk"] = "Low"
        return finding

    weights = [WEIGHTS.get(e.get("relationship", ""), 0.1) for e in edges]
    avg = sum(weights) / len(weights)

    hops = finding.get("hops", len(edges))
    score = round(avg * _length_factor(hops) * _tier_factor(finding.get("target_name", "")), 4)

    finding["score"] = score
    if score >= 0.55:
        finding["risk"] = "High"
    elif score >= 0.30:
        finding["risk"] = "Review"
    else:
        finding["risk"] = "Low"
    return finding


def analyze_graph(graph, max_hops=8, max_paths=5):
    """Stage 2 entry point. Returns a summary dict with ranked findings."""
    from analysis.paths import find_paths_to_targets
    from collection.schema import USER, COMPUTER, is_privileged_name

    targets = {n["id"] for n in graph["nodes"] if is_privileged_name(n["name"])}
    starts = {
        n["id"] for n in graph["nodes"]
        if n["kind"] in (USER, COMPUTER) and not is_privileged_name(n["name"])
    }

    raw = find_paths_to_targets(graph, starts, targets, max_hops, max_paths)
    scored = [score_finding(f) for f in raw]
    scored.sort(key=lambda f: (-f["score"], f.get("hops", 99)))

    high = [f for f in scored if f["risk"] == "High"]
    review = [f for f in scored if f["risk"] == "Review"]

    return {
        "node_count": len(graph["nodes"]),
        "edge_count": len(graph["edges"]),
        "privileged_target_count": len(targets),
        "start_count": len(starts),
        "path_count": len(scored),
        "high_count": len(high),
        "review_count": len(review),
        "findings": scored[:200],
    }
