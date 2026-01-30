import unittest
import json
import hashlib
from stp.governor import STPKernel, SolvencyZone
from auditor import InternalEarAuditor

class MockVectorEngine:
    """Mock for deterministic vector generation."""
    def embed(self, text):
        # Returns a normalized dummy vector based on text hash
        val = int(hashlib.md5(text.encode()).hexdigest(), 16) % 100
        vec = np.zeros(64)
        vec[0] = val / 100.0
        return vec / np.linalg.norm(vec)

class TestHelicalLedger(unittest.TestCase):
    def setUp(self):
        self.constraint = "Hard Logical Coherence: STP v2.0"
        self.auditor = InternalEarAuditor(vector_engine=MockVectorEngine())
        self.kernel = STPKernel(constraint=self.constraint, auditor=self.auditor)

    def test_genesis_anchor(self):
        """Verify KEYFRAME_COMMIT at t=0."""
        genesis = self.kernel.ledger[0]
        self.assertEqual(genesis["frame_type"], "KEYFRAME_COMMIT") [cite: 131, 232]
        self.assertEqual(genesis["prev_commit"], "0" * 64)
        self.assertIn("delta_commit", genesis)

    def test_hash_chain_integrity(self):
        """Verify that every frame is chained to the previous commit."""
        # Simulate 5 turns with alternating drift
        for i in range(5):
            self.kernel._emit_frame("DELTA_BRIDGE", {"step": i, "payload": "reconciliation"}) [cite: 244]
            
        for i in range(1, len(self.kernel.ledger)):
            current = self.kernel.ledger[i]
            previous = self.kernel.ledger[i-1]
            # Rule: current.prev_commit MUST match previous.delta_commit
            self.assertEqual(current["prev_commit"], previous["delta_commit"]) [cite: 161, 251]

    def test_canonical_determinism(self):
        """Ensure canonicalization prevents hash divergence from whitespace/order."""
        data_a = {"z": 1, "a": 2}
        data_b = {"a": 2, "z": 1}
        self.assertEqual(self.kernel.canonical_hash(data_a), self.kernel.canonical_hash(data_b)) [cite: 145]

    def test_lambda_return_artifact(self):
        """Verify DELTA_RETURN frame structure and tether."""
        self.kernel.apply_phased_return(current_variance=0.08) [cite: 101, 245]
        last_frame = self.kernel.ledger[-1]
        self.assertEqual(last_frame["frame_type"], "DELTA_RETURN") [cite: 248]
        self.assertEqual(last_frame["payload"]["return_step"]["target"], "origin") [cite: 253]

if __name__ == "__main__":
    import numpy as np
    unittest.main()
