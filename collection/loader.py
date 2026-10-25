import io
import json
import zipfile
from pathlib import PurePosixPath

from collection.schema import normalize_kind


_REL_MAP = {
    "memberof":            "MemberOf",
    "adminto":             "AdminTo",
    "canrdp":              "CanRDP",
    "hassession":          "HasSession",
    "genericall":          "GenericAll",
    "genericwrite":        "GenericWrite",
    "writedacl":           "WriteDacl",
    "writeowner":          "WriteOwner",
    "forcechangepassword": "ForceChangePassword",
    "addmember":           "AddMember",
    "allextendedrights":   "AllExtendedRights",
    "getchanges":          "GetChanges",
    "getchangesall":       "GetChangesAll",
    "allowedtoact":        "AllowedToAct",
    "allowedtodelegate":   "AllowedToDelegate",
    "gplink":              "GPLink",
    "trustedby":           "TrustedBy",
}


def _normalize_rel(name):
    key = str(name or "").lower().replace("_", "").replace("-", "").strip()
    return _REL_MAP.get(key, name or "RELATED_TO")


def _node_from(item):
    """Pull a (id, name, kind) tuple out of a SharpHound entry. Returns
    None if there's no identifier we can key on."""
    props = item.get("Properties") or {}
    oid = (item.get("ObjectIdentifier") or item.get("id")
           or props.get("objectid") or props.get("objectsid"))
    if not oid:
        return None
    name = (props.get("name") or props.get("samaccountname")
            or props.get("displayname") or oid)
    kind = normalize_kind(item.get("type") or item.get("kind"))
    return {"id": str(oid), "name": str(name), "kind": kind}


def _edges_from(item, source_id):
    """SharpHound splits relationships across several arrays depending on
    the collection method used. We handle the common ones."""
    out = []

    for ace in item.get("Aces") or []:
        if not isinstance(ace, dict):
            continue
        target = (ace.get("ObjectIdentifier") or ace.get("MemberId")
                  or ace.get("PrincipalSID"))
        if target:
            out.append({
                "source": source_id,
                "target": str(target),
                "relationship": _normalize_rel(ace.get("RightName") or "GenericAll"),
            })

    for member in item.get("Members") or []:
        if isinstance(member, dict):
            target = member.get("ObjectIdentifier") or member.get("MemberId")
            if target:
                out.append({"source": source_id, "target": str(target),
                            "relationship": "MemberOf"})

  
    for sess in item.get("Sessions") or []:
        if isinstance(sess, dict):
            user = sess.get("UserSID") or sess.get("User")
            computer = sess.get("ComputerSID") or sess.get("Computer")
            if user and computer:
                out.append({"source": str(user), "target": str(computer),
                            "relationship": "HasSession"})

    return out


def _consume(graph, items):
    for item in items or []:
        if not isinstance(item, dict):
            continue
        node = _node_from(item)
        if not node:
            continue
        graph["nodes"][node["id"]] = node
        for e in _edges_from(item, node["id"]):
            graph["edges"].append(e)


def _finalize(graph):
    """Dedup edges, add placeholder nodes for anything referenced but not
    defined (foreign SIDs, unresolved trustees), and return the shape."""
    ids = set(graph["nodes"].keys())
    seen = set()
    edges = []

    for e in graph["edges"]:
        s, t = str(e["source"]), str(e["target"])
        if s == t:
            continue
        for m in (s, t):
            if m not in ids:
                graph["nodes"][m] = {"id": m, "name": m, "kind": "Unknown"}
                ids.add(m)
        key = (s, t, e["relationship"])
        if key in seen:
            continue
        seen.add(key)
        edges.append({"source": s, "target": t, "relationship": e["relationship"]})

    return {
        "nodes": list(graph["nodes"].values()),
        "edges": edges,
        "notes": graph["notes"],
    }


def load_export(filename, raw):
    
    graph = {"nodes": {}, "edges": [], "notes": []}
    suffix = PurePosixPath(filename).suffix.lower()

    if suffix == ".zip":
        try:
            zf = zipfile.ZipFile(io.BytesIO(raw))
        except zipfile.BadZipFile:
            raise ValueError("not a valid zip file")
        jsons = [i for i in zf.infolist()
                 if not i.is_dir() and i.filename.lower().endswith(".json")]
        if not jsons:
            raise ValueError("zip contains no .json files")
        for info in jsons:
            if ".." in PurePosixPath(info.filename).parts:
                graph["notes"].append("skipped unsafe path: " + info.filename)
                continue
            try:
                obj = json.loads(zf.read(info).decode("utf-8-sig"))
            except Exception:
                graph["notes"].append("could not parse " + info.filename)
                continue
            _consume(graph, obj if isinstance(obj, list) else obj.get("data", []))

    elif suffix == ".json":
        try:
            obj = json.loads(raw.decode("utf-8-sig"))
        except Exception as exc:
            raise ValueError("bad json: " + str(exc))

        # Vanguard native shape passes straight through.
        if isinstance(obj, dict) and "nodes" in obj and "edges" in obj:
            for n in obj["nodes"]:
                nid = str(n.get("id") or n.get("name"))
                graph["nodes"][nid] = {
                    "id": nid,
                    "name": n.get("name") or nid,
                    "kind": normalize_kind(n.get("kind") or n.get("type")),
                }
            for e in obj["edges"]:
                graph["edges"].append({
                    "source": str(e["source"]),
                    "target": str(e["target"]),
                    "relationship": _normalize_rel(e.get("relationship")),
                })
        else:
            _consume(graph, obj if isinstance(obj, list) else obj.get("data", []))
    else:
        raise ValueError("only .json and .zip are accepted")

    result = _finalize(graph)
    if not result["nodes"]:
        raise ValueError("no recognizable nodes in export")
    return result
