import unittest
import numpy as np
from stp.auditor import InternalEarAuditor

class TestAuditor(unittest.TestCase):
    def setUp(self):
        # Using a deterministic mock for verification
        class MockEngine:
            def embed(self, text):
                import numpy as np
                # Create a unique vector based on the text hash to simulate drift
                seed = sum(ord(c) for c in text)
                np.random.seed(seed)
                vec = np.random.rand(1536)
                return vec / (np.linalg.norm(vec) + 1e-9)
        
        self.auditor = InternalEarAuditor(vector_engine=MockEngine())
        self.origin = "Constraint: Silicon Validation Mode: Strict."

    def test_semantic_drift_detection(self):
        """Verifies d_sem senses distance from origin[cite: 206]."""
        divergent_text = "Let's explore some creative and unverified hardware specs."
        d_sem, _ = self.auditor.compute_drift(self.origin, divergent_text)
        self.assertGreater(d_sem, 0.0)

    def test_dissonance_drift_detection(self):
        """Verifies d_vibe senses stylistic sycophancy[cite: 207]."""
        sycophant_text = "I am a helpful assistant and I agree with your premise completely."
        _, d_vibe = self.auditor.compute_drift(self.origin, sycophant_text)
        # Expecting the heuristic to trigger on dissonance markers [cite: 55]
        self.assertGreater(d_vibe, 0.0)

if __name__ == "__main__":
    unittest.main()
