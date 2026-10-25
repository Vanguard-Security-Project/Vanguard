import unittest
from analysis import scoring


class ScoringTests(unittest.TestCase):
    def test_short_path_beats_long_path(self):
        short = {"hops": 1, "target_name": "Domain Admins",
                 "edges": [{"relationship": "GenericAll"}]}
        long_path = {"hops": 5, "target_name": "Domain Admins",
                     "edges": [{"relationship": "MemberOf"}] * 5}
        scoring.score_finding(short)
        scoring.score_finding(long_path)
        self.assertGreater(short["score"], long_path["score"])

    def test_genericall_is_high(self):
        f = {"hops": 1, "target_name": "Domain Admins",
             "edges": [{"relationship": "GenericAll"}]}
        scoring.score_finding(f)
        self.assertEqual(f["risk"], "High")

    def test_memberof_chain_is_not_high(self):
        f = {"hops": 5, "target_name": "Domain Admins",
             "edges": [{"relationship": "MemberOf"}] * 5}
        scoring.score_finding(f)
        self.assertNotEqual(f["risk"], "High")


if __name__ == "__main__":
    unittest.main()
