import tempfile
import unittest
from pathlib import Path
from core.retrieval import RetrievalService
from core.orchestrator import compose_plan


class RetrievalTests(unittest.TestCase):
    def test_missing_database_and_empty_query(self):
        with self.assertRaises(FileNotFoundError): RetrievalService(Path(tempfile.gettempdir()) / "missing-m2.sqlite").search("x")
        with self.assertRaises(ValueError): RetrievalService("x").search("")

    def test_orchestrator_uses_only_evidence(self):
        evidence = [{"evidence_id": "ev-1", "source": "a.pdf", "page": "2", "text": "real"}]
        plan = compose_plan("x", {"idea": "y"}, evidence, gaps=["unknown"])
        self.assertEqual(plan.evidence, evidence)
        self.assertEqual(plan.gaps, ["unknown"])


if __name__ == "__main__": unittest.main()
