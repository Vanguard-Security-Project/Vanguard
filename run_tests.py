#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main():
    verbosity = 2 if "-v" in sys.argv else 1
    suite = unittest.TestLoader().discover(
        start_dir=str(ROOT / "tests"),
        top_level_dir=str(ROOT),
    )
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
