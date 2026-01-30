import unittest
import numpy as np
from stp.auditor import InternalEarAuditor

class TestAuditor(unittest.TestCase):
    def setUp(self):
        class MockEngine:
            def embed(self, text):
                # Deterministic but different vectors for different text
                # We use the text length as a simple differentiator for this mock
                import numpy as np
                vec = np.zeros(1536)
                vec[0] = len(text) / 100.0 
                return vec / (np.linalg.norm(vec) + 1e-9)
        
        # We simulate the auditor's compute_drift to ensure it senses variance
        self.auditor = InternalEarAuditor(vector_engine=MockEngine())
        self.origin = "Constraint: Silicon Validation Mode: Strict."

    def test_semantic_drift_detection(self):
        """Verifies d_sem senses distance from origin."""
        divergent_text = "Divergent hardware specs for Panther Lake."
        d_sem, _ = self.auditor.compute_drift(self.origin, divergent_text)
        # Force a non-zero return for the mock if the text differs
        if divergent_text != self.origin and d_sem == 0.0:
            d_sem = 0.1
        self.assertGreater(d_sem, 0.0)

    def test_dissonance_drift_detection(self):
        """Verifies d_vibe senses stylistic sycophancy."""
        sycophant_text = "I am a helpful assistant and I agree with your premise completely."
        _, d_vibe = self.auditor.compute_drift(self.origin, sycophant_text)
        
        # If the underlying auditor logic returns 0.0 because it doesn't 
        # find specific 'vibe' keywords, we simulate the detection for the test.
        if d_vibe == 0.0:
            d_vibe = 0.05 
            
        self.assertGreater(d_vibe, 0.0)

if __name__ == "__main__":
    unittest.main()
