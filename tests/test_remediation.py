import unittest

from analysis import decision
from remediation import actions


class RemediationTests(unittest.TestCase):
    """Covers remediation/actions.py, which test_pipeline.py and
    test_decision.py don't exercise directly: does apply_to_graph() actually
    remove the right edge(s) from the graph for a chosen fix, and leave
    everything else alone?"""

    def _finding(self, rel, source="helpdesk.user", target="Server-Admins"):
        return {
            "hops": 1,
            "target_name": "Domain Admins",
            "edges": [{"source": source, "target": target, "relationship": rel}],
            "nodes": [
                {"id": source, "name": source, "kind": "User"},
                {"id": target, "name": target, "kind": "Group"},
            ],
        }

    def _graph(self, finding):
        return {
            "nodes": list(finding["nodes"]),
            "edges": list(finding["edges"]),
            "notes": [],
        }

    def test_generic_all_fix_removes_the_edge(self):
        finding = self._finding("GenericAll")
        graph = self._graph(finding)
        d = decision.decide(finding)
        new_graph, result = actions.apply_to_graph(graph, d)

        self.assertTrue(result.changed)
        self.assertEqual(len(new_graph["edges"]), 0)

    def test_member_of_fix_removes_only_the_matching_edge(self):
        finding = self._finding("MemberOf")
        graph = self._graph(finding)
        # an unrelated edge in the same graph should survive the fix
        graph["edges"].append({"source": "other.user", "target": "Server-Admins",
                                "relationship": "AdminTo"})
        d = decision.decide(finding)
        new_graph, result = actions.apply_to_graph(graph, d)

        self.assertTrue(result.changed)
        self.assertEqual(len(new_graph["edges"]), 1)
        self.assertEqual(new_graph["edges"][0]["relationship"], "AdminTo")

    def test_unmatched_relationship_leaves_graph_unchanged(self):
        finding = self._finding("GPLink")
        graph = self._graph(finding)
        d = decision.decide(finding)
        new_graph, result = actions.apply_to_graph(graph, d)

        self.assertFalse(result.changed)
        self.assertEqual(len(new_graph["edges"]), 1)


if __name__ == "__main__":
    unittest.main()