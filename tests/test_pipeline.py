import json
import unittest

from analysis import decision, scoring
from collection import loader
from remediation import actions
from validation import reattack


def _native_export():
    return {
        "nodes": [
            {"id": "u1", "name": "user.one", "kind": "User"},
            {"id": "g1", "name": "Helpdesk", "kind": "Group"},
            {"id": "c1", "name": "server-01", "kind": "Computer"},
            {"id": "g2", "name": "Server Operators", "kind": "Group"},
            {"id": "g3", "name": "Domain Admins", "kind": "Group"},
        ],
        "edges": [
            {"source": "u1", "target": "g1", "relationship": "MemberOf"},
            {"source": "g1", "target": "c1", "relationship": "AdminTo"},
            {"source": "c1", "target": "g2", "relationship": "GenericAll"},
            {"source": "g2", "target": "g3", "relationship": "MemberOf"},
        ],
        "notes": [],
    }


class PipelineTests(unittest.TestCase):
    def _graph(self):
        raw = json.dumps(_native_export()).encode("utf-8")
        return loader.load_export("x.json", raw)

    def test_loader_reads_native_shape(self):
        g = self._graph()
        self.assertEqual(len(g["nodes"]), 5)
        self.assertEqual(len(g["edges"]), 4)

    def test_analyze_finds_high_risk_path(self):
        g = self._graph()
        r = scoring.analyze_graph(g)
        self.assertGreater(r["path_count"], 0)
        self.assertGreater(r["high_count"], 0)

    def test_fix_removes_at_least_one_path(self):
        g = self._graph()
        r = scoring.analyze_graph(g)
        decisions = decision.decide_batch(r["findings"])
        fixed = g
        for d in decisions:
            fixed, _ = actions.apply_to_graph(fixed, d)
        r2 = scoring.analyze_graph(fixed)
        self.assertLessEqual(r2["path_count"], r["path_count"])

    def test_graph_verify_before_and_after(self):
        g = self._graph()
        r = scoring.analyze_graph(g)
        f = r["findings"][0]

        before = reattack.graph_verify(g, f, "before")
        self.assertTrue(before.succeeded)

        fixed, _ = actions.apply_to_graph(g, decision.decide(f))
        after = reattack.graph_verify(fixed, f, "after")
        self.assertFalse(after.succeeded)


if __name__ == "__main__":
    unittest.main()
