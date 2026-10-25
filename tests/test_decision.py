import unittest
from analysis import decision


class DecisionTests(unittest.TestCase):
    def _finding(self, rel):
        return {
            "hops": 1,
            "target_name": "Domain Admins",
            "edges": [{"source": "a", "target": "b", "relationship": rel}],
            "nodes": [
                {"id": "a", "name": "alice"},
                {"id": "b", "name": "Domain Admins"},
            ],
        }

    def test_memberof_picks_remove_member(self):
        d = decision.decide(self._finding("MemberOf"))
        self.assertEqual(d["chosen"]["kind"], "RemoveMember")

    def test_genericall_picks_dacl(self):
        d = decision.decide(self._finding("GenericAll"))
        self.assertEqual(d["chosen"]["kind"], "RemoveDaclAce")

    def test_admin_to_picks_local_admin(self):
        d = decision.decide(self._finding("AdminTo"))
        self.assertEqual(d["chosen"]["kind"], "RemoveLocalAdmin")

    def test_unknown_relationship_returns_none(self):
        d = decision.decide(self._finding("SomethingWeird"))
        self.assertIsNone(d["chosen"])


if __name__ == "__main__":
    unittest.main()
