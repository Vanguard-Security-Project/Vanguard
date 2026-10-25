from dataclasses import dataclass, field

@dataclass
class ActionResult:
    kind: str
    principal: str = ""
    target: str = ""
    removed_edges: list = field(default_factory=list)
    changed: bool = False
    note: str = ""


_REMOVES = {
    "RemoveMember":     {"MemberOf"},
    "RemoveLocalAdmin": {"AdminTo"},
    "RemoveDaclAce":    {"GenericAll", "GenericWrite", "WriteDacl",
                         "WriteOwner", "ForceChangePassword", "AddMember",
                         "AllExtendedRights", "GetChanges", "GetChangesAll"},
    "RemoveDelegation": {"AllowedToDelegate", "AllowedToAct"},
    "RemoveRBCD":       {"RBCD"},
}


def apply_to_graph(graph, decision):
    chosen = decision.get("chosen")
    ctx = decision.get("context", {})

    if not chosen:
        return graph, ActionResult(kind="none", note="no fix chosen")

    rels = _REMOVES.get(chosen["kind"], set())
    to_remove = {
        (e["source"], e["target"], e["relationship"])
        for e in decision["finding"].get("edges", [])
        if e["relationship"] in rels
    }

    new_edges = [
        e for e in graph["edges"]
        if (e["source"], e["target"], e["relationship"]) not in to_remove
    ]

    new_graph = {
        "nodes": list(graph["nodes"]),
        "edges": new_edges,
        "notes": list(graph.get("notes", [])),
    }

    return new_graph, ActionResult(
        kind=chosen["kind"],
        principal=ctx.get("principal", ""),
        target=ctx.get("target", ""),
        removed_edges=[list(t) for t in to_remove],
        changed=len(to_remove) > 0,
        note="removed {} edge(s)".format(len(to_remove)),
    )
