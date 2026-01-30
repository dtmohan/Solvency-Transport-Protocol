import numpy as np
from typing import Tuple, Dict

class InternalEarAuditor:
    """
    STP v2.0 Auditor. 
    Computes drift signals (d_sem, d_vibe) relative to session origin.
    """
    def __init__(self, vector_engine):
        self.engine = vector_engine

    def compute_drift(self, origin_text: str, candidate_text: str) -> Tuple[float, float]:
        """
        Calculates two-channel drift[cite: 204].
        Input: C (origin) and candidate at t=N[cite: 219].
        """
        # 1. Semantic Drift (d_sem) [cite: 206]
        v_origin = self.engine.embed(origin_text)
        v_candidate = self.engine.embed(candidate_text)
        
        # Cosine distance: 1 - (A·B / ||A||||B||) [cite: 166]
        d_sem = 1.0 - np.dot(v_origin, v_candidate) / (
            np.linalg.norm(v_origin) * np.linalg.norm(v_candidate)
        )

        # 2. Dissonance Drift (d_vibe) [cite: 207]
        # In prod, this uses a smaller model or heuristic style-checker.
        # Here we use a surrogate proxy for vibe/tone deviation.
        d_vibe = self._detect_stylistic_dissonance(candidate_text)

        return float(d_sem), float(d_vibe)

    def _detect_stylistic_dissonance(self, text: str) -> float:
        """Heuristic proxy for vibe drift (e.g., tone/intrusion)[cite: 89]."""
        # Checks for common "unpriced deviations" like sycophancy or fluff.
        dissonance_markers = ["I hope this helps", "As an AI", "emotional appeal"]
        count = sum(1 for m in dissonance_markers if m in text)
        return min(1.0, count * 0.2)
