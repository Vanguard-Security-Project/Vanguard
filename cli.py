#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

from analysis import decision, scoring
from collection import loader
from collection import neo4j_client as neo
from remediation import actions, planner
from validation import reattack


def _load(path):
    return loader.load_export(path.name, path.read_bytes())


def cmd_analyze(args):
    graph = _load(Path(args.file))
    result = scoring.analyze_graph(graph)

    print("Nodes: {}  Edges: {}".format(result["node_count"], result["edge_count"]))
    print("Privileged targets: {}  Start nodes: {}".format(
        result["privileged_target_count"], result["start_count"]))
    print("Findings: {}  ({} high, {} review)".format(
        result["path_count"], result["high_count"], result["review_count"]))

    if result["path_count"] == 0:
        print("\nNo paths found. Not proof of safety - check collection scope.")
        return 0

    print()
    for f in result["findings"][:args.limit]:
        sig = " -> ".join(n["name"] for n in f["nodes"])
        print("[{}] score={}  {}".format(f["risk"], f["score"], sig))
    return 0


def cmd_decide(args):
    graph = _load(Path(args.file))
    result = scoring.analyze_graph(graph)
    decisions = decision.decide_batch(result["findings"])
    plan = planner.generate_plan(decisions, out_dir=args.out_dir)

    print("Actions: {}".format(plan["action_count"]))
    print("Apply:    {}".format(plan["apply_script"]))
    print("Rollback: {}".format(plan["rollback_script"]))
    return 0


def cmd_pipeline(args):
    graph = _load(Path(args.file))

    print("STAGE 1 - SCAN")
    print("  nodes: {}  edges: {}".format(len(graph["nodes"]), len(graph["edges"])))

    print("\nSTAGE 2 - ANALYZE")
    result = scoring.analyze_graph(graph)
    print("  findings: {}  ({} high, {} review)".format(
        result["path_count"], result["high_count"], result["review_count"]))
    for f in result["findings"][:5]:
        print("  [{}] score={}  {}".format(
            f["risk"], f["score"],
            " -> ".join(n["name"] for n in f["nodes"])))

    print("\nSTAGE 3+4 - FIX")
    decisions = decision.decide_batch(result["findings"][:10])
    plan = planner.generate_plan(decisions, out_dir=args.out_dir)
    print("  actions:  {}".format(plan["action_count"]))
    print("  apply:    {}".format(plan["apply_script"]))
    print("  rollback: {}".format(plan["rollback_script"]))

    fixed = graph
    for d in decisions:
        fixed, _ = actions.apply_to_graph(fixed, d)

    print("\nSTAGE 4 - RE-ATTACK (before)")
    for f in result["findings"][:10]:
        res = reattack.graph_verify(graph, f, "before")
        print("  [{}] {} -> {}".format(
            "present" if res.succeeded else "absent",
            f["start_name"], f["target_name"]))

    print("\nSTAGE 5 - VERIFY (after)")
    verified = 0
    for f in result["findings"][:10]:
        res = reattack.graph_verify(fixed, f, "after")
        verdict = "verified_fixed" if not res.succeeded else "still_vulnerable"
        if not res.succeeded:
            verified += 1
        print("  [{}] {} -> {}".format(verdict, f["start_name"], f["target_name"]))
    print("\n  verified: {}/{}".format(verified, len(result["findings"][:10])))

    print("\nRE-ANALYSIS")
    reanalysis = scoring.analyze_graph(fixed)
    print("  paths after fix: {} (was {})".format(
        reanalysis["path_count"], result["path_count"]))

    out = Path(args.report)
    out.write_text(json.dumps({
        "source": {"filename": args.file,
                   "nodes": len(graph["nodes"]),
                   "edges": len(graph["edges"])},
        "analysis": result,
        "plan": plan,
        "reanalysis": reanalysis,
    }, indent=2, default=str), encoding="utf-8")
    print("\nReport: {}".format(out))
    return 0


def cmd_load(args):
    if not neo.is_available():
        print("Neo4j is not reachable. Set VANGUARD_NEO4J_URI/USER/PASS.")
        return 1
    graph = _load(Path(args.file))
    neo.ensure_constraints()
    nodes = [{"id": n["id"], "name": n["name"], "kind": n["kind"]}
             for n in graph["nodes"]]
    n_written = neo.write_nodes(nodes)
    e_written = neo.write_edges(graph["edges"])
    print("Wrote {} nodes, {} edges.".format(n_written, e_written))
    print("Graph totals: {}".format(neo.counts()))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="vanguard")
    sub = parser.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze")
    a.add_argument("file")
    a.add_argument("--limit", type=int, default=20)
    a.set_defaults(func=cmd_analyze)

    d = sub.add_parser("decide")
    d.add_argument("file")
    d.add_argument("--out-dir", default="plans")
    d.set_defaults(func=cmd_decide)

    p = sub.add_parser("pipeline")
    p.add_argument("file")
    p.add_argument("--out-dir", default="plans")
    p.add_argument("--report", default="vanguard-report.json")
    p.set_defaults(func=cmd_pipeline)

    ld = sub.add_parser("load")
    ld.add_argument("file")
    ld.set_defaults(func=cmd_load)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
