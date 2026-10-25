import os

try:
    from neo4j import GraphDatabase
    _HAVE_DRIVER = True
except ImportError:
    GraphDatabase = None
    _HAVE_DRIVER = False


_URI = os.environ.get("VANGUARD_NEO4J_URI", "bolt://localhost:7687")
_USER = os.environ.get("VANGUARD_NEO4J_USER", "neo4j")
_PASS = os.environ.get("VANGUARD_NEO4J_PASS", "vanguard-local")

_driver = None


def _get():
    global _driver
    if not _HAVE_DRIVER:
        return None
    if _driver is None:
        try:
            _driver = GraphDatabase.driver(_URI, auth=(_USER, _PASS))
            _driver.verify_connectivity()
        except Exception:
            _driver = None
    return _driver


def is_available():
    return _get() is not None


def _session():
    drv = _get()
    if drv is None:
        raise RuntimeError("Neo4j is not reachable")
    return drv.session()


def run(cypher, **params):
    with _session() as s:
        return [dict(r) for r in s.run(cypher, **params)]


def write_nodes(nodes):
    
    if not nodes:
        return 0
    cypher = """
    UNWIND $nodes AS n
    MERGE (p:Principal {id: n.id})
    SET p.name = n.name, p.kind = n.kind
    RETURN count(p) AS c
    """
    with _session() as s:
        rec = s.run(cypher, nodes=nodes).single()
        return rec["c"] if rec else 0


def write_edges(edges):
    if not edges:
        return 0
    cypher = """
    UNWIND $edges AS e
    MATCH (a:Principal {id: e.source})
    MATCH (b:Principal {id: e.target})
    MERGE (a)-[r:REL {kind: e.relationship}]->(b)
    RETURN count(r) AS c
    """
    with _session() as s:
        rec = s.run(cypher, edges=edges).single()
        return rec["c"] if rec else 0


def wipe():
    with _session() as s:
        s.run("MATCH (n) DETACH DELETE n")


def counts():
    with _session() as s:
        n = s.run("MATCH (n:Principal) RETURN count(n) AS c").single()["c"]
        e = s.run("MATCH ()-[r:REL]->() RETURN count(r) AS c").single()["c"]
        return {"nodes": n, "edges": e}


def ensure_constraints():
    with _session() as s:
        s.run("CREATE CONSTRAINT principal_id IF NOT EXISTS "
              "FOR (p:Principal) REQUIRE p.id IS UNIQUE")
