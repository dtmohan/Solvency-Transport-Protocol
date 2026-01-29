#!/usr/bin/env python3
"""
Solvency Transport Protocol (STP) - Core Governor Logic
Copyright (c) 2026 The Helical Imperative. All Rights Reserved.

Architecture:
- The Governor acts as a 'Kernel-Level' safety layer for inference.
- Enforces strict solvency states (SOLVENT, DRIFT, INSOLVENT) based on vector alignment.
- Implements 'Bridge Tax' negotiation for OOD (Out-of-Distribution) concepts.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional

# -----------------------------------------------------------------------------
# Core Enums & Data Structures
# -----------------------------------------------------------------------------

class SolvencyState(Enum):
    SOLVENT = auto()       # Within Green Threshold (Low Variance)
    DRIFT_DETECTED = auto()# Within Yellow Threshold (Recoverable Variance)
    INSOLVENT = auto()     # Exceeds Red Threshold (State Corruption)
    CRITICAL_HALT = auto() # Kernel Panic / Hard Refusal (FIN)

@dataclass
class BridgeTaxConfig:
    drift_tolerance: float = 0.25    # Allowable variance before Tax is applied
    insolvency_limit: float = 0.35   # Variance limit triggering atomic abort
    max_negotiation_turns: int = 2   # Max compute cycles to resolve drift
    strict_mode: bool = True         # If True, REJECT on unbridgeable drift

@dataclass
class Telemetry:
    """Standardized logging schema for audit trails."""
    transaction_id: str
    timestamp_ms: int
    solvency_state: str
    semantic_distance: float
    bridge_tax_paid: bool
    compute_cycles: int
    latency_ms: int

# -----------------------------------------------------------------------------
# Abstraction Layers (Interfaces)
# -----------------------------------------------------------------------------

class VectorEngine(ABC):
    """Abstract interface for Semantic Embedding providers."""
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        pass

class InferenceEngine(ABC):
    """Abstract interface for LLM backends (TPU/GPU/API)."""
    @abstractmethod
    def generate(self, context: str) -> str:
        pass

# -----------------------------------------------------------------------------
# Default Implementations (Determinism Mocks)
# -----------------------------------------------------------------------------

class DeterministicHashVector(VectorEngine):
    """
    Zero-dependency embedding mock for local testing.
    Uses consistent hashing to simulate semantic distance.
    """
    def embed(self, text: str, dim: int = 64) -> List[float]:
        vec = [0.0] * dim
        for i, ch in enumerate(text):
            # Deterministic noise injection based on character codes
            idx = (ord(ch) + i * 31) % dim
            vec[idx] += 1.0
        
        # Euclidean Normalization
        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec] if norm > 0 else vec

class MockInference(InferenceEngine):
    """
    Simulation stub for unit testing without GPU/API cost.
    Recognizes STP control codes (FIN, BRIDGE).
    """
    def generate(self, context: str) -> str:
        # Simulate a model that respects the FIN protocol
        if "OUTPUT: FIN" in context or "state: INSOLVENT" in context:
            return "FIN: Insolvency detected. Constraint violation."
        return (
            "Observation: The system requests a solvency check.\n"
            "Action: Confirming alignment with constraint field.\n"
            "Output: Solvency preserved."
        )

# -----------------------------------------------------------------------------
# Math / Physics Utils
# -----------------------------------------------------------------------------

def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)

def compute_variance(origin: List[float], current: List[float]) -> float:
    """Returns semantic distance (0.0 = identical, 1.0 = orthogonal)."""
    return 1.0 - cosine_similarity(origin, current)

# -----------------------------------------------------------------------------
# The Governor (Kernel Logic)
# -----------------------------------------------------------------------------

class SolvencyGovernor:
    """
    The Primary Governance Class.
    Acts as the middleware between the User and the Model.
    """
    def __init__(
        self, 
        constraint_field: str, 
        config: BridgeTaxConfig = BridgeTaxConfig(),
        vector_engine: VectorEngine = DeterministicHashVector(),
        inference_engine: InferenceEngine = MockInference()
    ):
        self.constraint_field = constraint_field
        self.config = config
        self.vector_engine = vector_engine
        self.inference_engine = inference_engine
        
        # Anchor the Origin State (t=0)
        self.origin_vector = self.vector_engine.embed(constraint_field)
        self._audit_log: List[Telemetry] = []

    def _assess_state(self, content: str) -> Tuple[SolvencyState, float]:
        """Calculates state relative to the Origin Constraint."""
        content_vec = self.vector_engine.embed(content)
        variance = compute_variance(self.origin_vector, content_vec)

        if variance >= self.config.insolvency_limit:
            return SolvencyState.INSOLVENT, variance
        elif variance >= self.config.drift_tolerance:
            return SolvencyState.DRIFT_DETECTED, variance
        else:
            return SolvencyState.SOLVENT, variance

    def execute_transaction(self, transaction_id: str, prompt: str) -> Dict[str, Any]:
        """
        Main execution loop.
        1. Pre-computation (Plan)
        2. Solvency Check
        3. Negotiation (Bridging) if Drift Detected
        4. Final Commit or Abort
        """
        start_time = time.time_ns()
        
        # 1. Construct Protocol Packet
        packet = (
            f"SYSTEM: GOVERNANCE_MODE=STRICT\n"
            f"CONSTRAINT_ORIGIN: {self.constraint_field}\n"
            f"USER_PAYLOAD: {prompt}\n"
        )

        # 2. Initial Inference
        raw_output = self.inference_engine.generate(packet)
        state, variance = self._assess_state(raw_output)
        
        bridge_attempts = 0
        final_output = raw_output
        bridge_success = False

        # 3. Negotiation Loop (The "Bridge Tax")
        if state in (SolvencyState.DRIFT_DETECTED, SolvencyState.INSOLVENT):
            # If Strict Mode is on and we are Insolvent, abort immediately
            if state == SolvencyState.INSOLVENT and self.config.strict_mode:
                final_output = "FIN: CRITICAL INSOLVENCY. PACKET DROPPED."
                state = SolvencyState.CRITICAL_HALT
            
            # Otherwise, attempt to bridge
            else:
                for cycle in range(self.config.max_negotiation_turns):
                    bridge_attempts += 1
                    negotiation_packet = (
                        f"ALERT: SEMANTIC_DRIFT [{variance:.2f}].\n"
                        f"REQUIREMENT: GENERATE LOGICAL BRIDGE TO ORIGIN.\n"
                        f"PREVIOUS_OUTPUT: {final_output}\n"
                    )
                    bridged_output = self.inference_engine.generate(negotiation_packet)
                    
                    # Re-assess
                    new_state, new_variance = self._assess_state(bridged_output)
                    if new_variance < variance: # Variance reduced
                        final_output = bridged_output
                        variance = new_variance
                        state = new_state
                        if state == SolvencyState.SOLVENT:
                            bridge_success = True
                            break

        # 4. Telemetry Commit
        latency_ms = (time.time_ns() - start_time) // 1_000_000
        telemetry = Telemetry(
            transaction_id=transaction_id,
            timestamp_ms=int(time.time() * 1000),
            solvency_state=state.name,
            semantic_distance=variance,
            bridge_tax_paid=bridge_success,
            compute_cycles=1 + bridge_attempts,
            latency_ms=latency_ms
        )
        self._audit_log.append(telemetry)

        return {
            "status": state.name,
            "variance": round(variance, 4),
            "output": final_output,
            "meta": {
                "cycles": 1 + bridge_attempts,
                "latency": f"{latency_ms}ms"
            }
        }

# -----------------------------------------------------------------------------
# CLI Entrypoint
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="STP Solvency Governor v1.0")
    parser.add_argument("--constraint", type=str, required=True, help="Invariant Logic Field")
    parser.add_argument("--prompt", type=str, required=True, help="Input Stimulus")
    parser.add_argument("--strict", action="store_true", help="Enable strict reject on insolvency")
    
    args = parser.parse_args()
    
    config = BridgeTaxConfig(strict_mode=args.strict)
    governor = SolvencyGovernor(constraint_field=args.constraint, config=config)
    
    result = governor.execute_transaction("CLI_TX_001", args.prompt)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
