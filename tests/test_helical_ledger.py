import os
import unittest
import json
import hashlib
import numpy as np
from stp.governor import STPKernel, SolvencyZone

class MockAuditor:
    def compute_drift(self, origin, candidate):
        # Returns a nominal drift of 0.01 to keep the session in the GREEN zone
        return 0.01, 0.01

class TestHelicalLedger(unittest.TestCase):
    def setUp(self):
        self.auditor = MockAuditor()
        self.config_path = "eval/deployment_config.json"
        
        # 1. Ensure the directory exists for the Recursive Truth Axis anchor
        os.makedirs("eval", exist_ok=True)
        
        # 2. Define the exact configuration required by governor.py
        self.test_config = {
            "protocol_version": "2.0-RFC",
            "governor_id": "test-kernel-001",
            "configuration": {
                "primary_invariant": "Silicon Validation Mode: Strict.",
                "bridge_tax_config": {
                    "drift_tolerance": 0.05,
                    "insolvency_limit": 0.15,
                    "return_policy": {"lambda": 0.25}
                }
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(self.test_config, f)
            
        self.kernel = STPKernel(config_path=self.config_path, auditor=self.auditor)

    def tearDown(self):
        # Clean up the temporary test configuration
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_genesis_anchor(self):
        """Verify KEYFRAME_COMMIT at t=0."""
        genesis = self.kernel.ledger[0]
        self.assertEqual(genesis["frame_type"], "KEYFRAME_COMMIT")
        self.assertEqual(genesis["prev_commit"], "0" * 64)
        self.assertIn("delta_commit", genesis)

    def test_hash_chain_integrity(self):
        """Verify that every frame is chained to the previous commit."""
        for i in range(5):
            self.kernel._emit_frame("DELTA_BRIDGE", {"step": i, "payload": "reconciliation"})
            
        for i in range(1, len(self.kernel.ledger)):
            current = self.kernel.ledger[i]
            previous = self.kernel.ledger[i-1]
            self.assertEqual(current["prev_commit"], previous["delta_commit"])

    def test_canonical_determinism(self):
        """Ensure canonicalization prevents hash divergence."""
        data_a = {"z": 1, "a": 2}
        data_b = {"a": 2, "z": 1}
        self.assertEqual(self.kernel.canonical_hash(data_a), self.kernel.canonical_hash(data_b))

    def test_lambda_return_artifact(self):
        """Verify DELTA_RETURN frame structure and tether."""
        self.kernel.apply_phased_return(current_variance=0.08)
        last_frame = self.kernel.ledger[-1]
        self.assertEqual(last_frame["frame_type"], "DELTA_RETURN")
        self.assertEqual(last_frame["payload"]["return_step"]["target"], "origin")

if __name__ == "__main__":
    unittest.main()
