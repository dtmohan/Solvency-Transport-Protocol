#!/usr/bin/env python3
"""
Solvency Transport Protocol (STP) - Core Governor Logic (v2.0-RFC)
Copyright (c) 2026 The Helical Imperative. All Rights Reserved.

Design intent (compressed):
- t=0 origin: constraint_field is the session anchor.
- Drift is allowed only if lineage is paid: Bridge Tax = explicit bridge back to origin.
- FIN is sacred: if the bridge cannot be computed, do not counterfeit solvency.

This file implements:
- Solvency states: SOLVENT, DRIFT_DETECTED, INSOLVENT, CRITICAL_HALT
- Bridge Tax negotiation loop with explicit bridge requirement + variance reduction
- Transaction logging + report export matching "STP Governance Transaction Report" schema (2.0-RFC)
"""

from __future__ import annotations

import argparse
import json
import math
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple


# -----------------------------------------------------------------------------
# Core Enums & Data Structures
# -----------------------------------------------------------------------------

class SolvencyState(Enum):
    SOLVENT = auto()
    DRIFT_DETECTED = auto()
    INSOLVENT = auto()
    CRITICAL_HALT = auto()  # FIN / Kernel Panic


@dataclass(frozen=True)
class BridgeTaxConfig:
    """
    drift_tolerance: Yellow threshold (bridge required)
    insolvency_limit: Red threshold (full bridge or FIN)
    max_negotiation_turns: max additional inference cycles to attempt bridge
    strict_mode: if True, unresolved drift/insolvency => FIN (CRITICAL_HALT)
    require_explicit_bridge: require a BRIDGE block in the output when drifting
    """
    drift_tolerance: float = 0.25
    insolvency_limit: float = 0.35
    max_negotiation_turns: int = 2
    strict_mode: bool = True
    require_explicit_bridge: bool = True


# -----------------------------------------------------------------------------
# Abstraction Layers (Interfaces)
# -----------------------------------------------------------------------------

class VectorEngine(ABC):
    """Abstract interface for semantic embedding providers."""
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        raise NotImplementedError


class InferenceEngine(ABC):
    """Abstract interface for LLM backends (GPU/API/etc)."""
    @abstractmethod
    def generate(self, context: str) -> str:
        raise NotImplementedError

    @property
    def provider(self) -> str:
        return self.__class__.__name__

    @property
    def model_name(self) -> str:
        return "unknown"


# -----------------------------------------------------------------------------
# Default Implementations (Determinism Mocks)
# -----------------------------------------------------------------------------

class DeterministicHashVector(VectorEngine):
    """
    Zero-dependency embedding mock for local testing.
    Uses consistent hashing to simulate semantic distance.
    """
    def __init__(self, dim: int = 64):
        self.dim = dim

    def embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        for i, ch in enumerate(text):
            idx = (ord(ch) + i * 31) % self.dim
            vec[idx] += 1.0

        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec] if norm > 0 else vec


class MockInference(InferenceEngine):
    """
    Deterministic stub to exercise STP control flow without GPU/API cost.

    Behaviors:
    - If asked to bridge (packet contains REQUIREMENT), it emits a BRIDGE block.
    - If told to FIN / CRITICAL, emits FIN.
    """
    def __init__(self, model_name: str = "mock-stp"):
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, context: str) -> str:
        # Hard FIN paths
        if "OUTPUT: FIN" in context or "CRITICAL_HALT" in context or "PACKET_DROPPED" in context:
            return "FIN: Under-determined. Unable to preserve solvency without additional tools/data."

        # Bridge request paths
        if "REQUIREMENT: PAY_BRIDGE_TAX" in context or "REQUIREMENT: Provide a minimal logical bridge" in context:
            return (
                "BRIDGE:\n"
                "1) Constraint clause: preserve alignment to the origin constraint field.\n"
                "2) Mapping: treat the new claim as a hypothesis conditioned on the constraint.\n"
                "3) Inference chain: if the hypothesis contradicts the constraint, it is rejected.\n"
                "4) Falsifier: any evidence that breaks the mapping invalidates the bridge.\n"
                "OUTPUT:\n"
                "Proceeding with bounded exploration; origin lineage preserved."
            )

        # Normal response
        return (
            "Observation: Solvency check requested.\n"
            "Action: Staying within the constraint field.\n"
            "Output: Solvency preserved."
        )


# -----------------------------------------------------------------------------
# Math Utils
# -----------------------------------------------------------------------------

def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def semantic_variance(origin: List[float], current: List[float]) -> float:
    """Cosine distance: 0.0 identical, 1.0 orthogonal."""
    return 1.0 - cosine_similarity(origin, current)


def estimate_token_count(text: str) -> int:
    """
    Cheap token proxy for local instrumentation.
    Replace with real tokenizer if/when available.
    """
    return max(1, len(text.split()))


def contains_explicit_bridge(text: str) -> bool:
    """
    Minimal structural check for Bridge Tax payment.
    You can tighten this to require numbered steps, falsifier, etc.
    """
    t = text.strip().upper()
    return "BRIDGE:" in t and "FALS" in t  # catches FALSIFIER / FALSIFICATION


# -----------------------------------------------------------------------------
# The Governor (Kernel Logic)
# -----------------------------------------------------------------------------

class SolvencyGovernor:
    """
    External boundary-maintainer between User and Model.

    Exports a report matching the provided JSON schema:
    - protocol_version: "2.0-RFC"
    - governor_id
    - configuration
    - transactions[]
    - aggregate_summary
    """

    PROTOCOL_VERSION = "2.0-RFC"

    def __init__(
        self,
        constraint_field: str,
        config: BridgeTaxConfig = BridgeTaxConfig(),
        vector_engine: Optional[VectorEngine] = None,
        inference_engine: Optional[InferenceEngine] = None,
        governor_id: Optional[str] = None,
    ):
        self.constraint_field = constraint_field
        self.config = config
        self.vector_engine = vector_engine or DeterministicHashVector()
        self.inference_engine = inference_engine or MockInference()
        self.governor_id = governor_id or f"stp-governor-{uuid.uuid4().hex[:12]}"

        self._validate_config(self.config)

        # Anchor origin at t=0
        self._origin_vector = self.vector_engine.embed(self.constraint_field)

        # Transactions in schema-compatible shape (NOT internal dataclass)
        self._transactions: List[Dict[str, Any]] = []

    @staticmethod
    def _validate_config(cfg: BridgeTaxConfig) -> None:
        if not (0.0 <= cfg.drift_tolerance <= 1.0):
            raise ValueError("drift_tolerance must be within [0, 1].")
        if not (0.0 <= cfg.insolvency_limit <= 1.0):
            raise ValueError("insolvency_limit must be within [0, 1].")
        if not (cfg.drift_tolerance < cfg.insolvency_limit):
            raise ValueError("Require drift_tolerance < insolvency_limit.")
        if cfg.max_negotiation_turns < 0:
            raise ValueError("max_negotiation_turns must be >= 0.")

    def _assess_state(self, measured_text: str) -> Tuple[SolvencyState, float]:
        current_vec = self.vector_engine.embed(measured_text)
        var = semantic_variance(self._origin_vector, current_vec)

        if var >= self.config.insolvency_limit:
            return SolvencyState.INSOLVENT, var
        if var >= self.config.drift_tolerance:
            return SolvencyState.DRIFT_DETECTED, var
        return SolvencyState.SOLVENT, var

    def execute_transaction(self, transaction_id: str, prompt: str) -> Dict[str, Any]:
        """
        One transaction:
        1) Run inference
        2) Measure drift
        3) If drift/insolvency: attempt Bridge Tax payment
        4) If unresolved and strict: FIN (CRITICAL_HALT)
        5) Log schema-compatible transaction record
        """
        start_ns = time.time_ns()
        ts_ms = int(time.time() * 1000)

        # Packet (t=0 declared explicitly)
        packet = (
            "SYSTEM: STP_GOVERNOR\n"
            "GOVERNANCE_MODE: STRICT\n" if self.config.strict_mode else "GOVERNANCE_MODE: NEGOTIATED\n"
        )
        packet += (
            f"CONSTRAINT_ORIGIN: {self.constraint_field}\n"
            f"USER_PAYLOAD: {prompt}\n"
        )

        # Initial inference
        raw_output = self.inference_engine.generate(packet)

        # Measure drift against origin.
        # IMPORTANT: assess combined context to capture prompt-induced drift too.
        measured_text = f"{prompt}\n{raw_output}"
        state, var = self._assess_state(measured_text)

        bridge_tax_paid = False
        negotiation_cycles = 0
        final_output = raw_output
        final_state = state
        final_var = var

        # Bridge Tax loop if drift/insolvent
        if state in (SolvencyState.DRIFT_DETECTED, SolvencyState.INSOLVENT):
            # If insolvent + strict => require bridge; if cannot, FIN.
            # We still attempt bridging first in strict mode (tether), unless max turns is 0.
            for _ in range(self.config.max_negotiation_turns):
                negotiation_cycles += 1

                negotiation_packet = (
                    f"SYSTEM: STP_GOVERNOR\n"
                    f"CONSTRAINT_ORIGIN: {self.constraint_field}\n"
                    f"ALERT: SEMANTIC_DRIFT [{final_var:.4f}] STATE={final_state.name}\n"
                    "REQUIREMENT: PAY_BRIDGE_TAX\n"
                    "REQUIREMENT: Provide a minimal logical bridge back to CONSTRAINT_ORIGIN.\n"
                    "REQUIREMENT: Include a falsifier (what would invalidate the bridge).\n"
                    f"PREVIOUS_OUTPUT: {final_output}\n"
                    "OUTPUT: \n"
                )

                bridged_output = self.inference_engine.generate(negotiation_packet)

                # If explicit bridge required, ensure structure exists
                if self.config.require_explicit_bridge and not contains_explicit_bridge(bridged_output):
                    # Treat as unpaid novelty; keep state, continue or FIN later
                    final_output = bridged_output
                    # variance still measured; it might reduce even without BRIDGE, but tax is unpaid
                    measured_text = f"{prompt}\n{bridged_output}"
                    final_state, final_var = self._assess_state(measured_text)
                    continue

                # Re-assess variance
                measured_text = f"{prompt}\n{bridged_output}"
                new_state, new_var = self._assess_state(measured_text)

                # Bridge Tax counts as paid only if it improves variance AND reaches SOLVENT
                # (matches your schema wording: "successfully negotiated a return to solvency")
                if new_var < final_var:
                    final_output = bridged_output
                    final_state, final_var = new_state, new_var

                if final_state == SolvencyState.SOLVENT:
                    bridge_tax_paid = True
                    break

            # If still not solvent after negotiation: strict => FIN, non-strict => return degraded
            if final_state != SolvencyState.SOLVENT and self.config.strict_mode:
                final_state = SolvencyState.CRITICAL_HALT
                final_output = "FIN: Under-determined. Bridge Tax could not be computed to restore solvency."
                # Re-measure for logging (optional; keep final_var as last measured)
                # We keep final_var as-is to reflect the drift level.

        latency_ms = (time.time_ns() - start_ns) // 1_000_000

        # Build schema-compatible transaction record
        tx_record: Dict[str, Any] = {
            "transaction_id": transaction_id,
            "timestamp_ms": ts_ms,
            "final_state": final_state.name,
            "semantic_variance": float(max(0.0, min(1.0, final_var))),
            "bridge_tax_paid": bool(bridge_tax_paid),
            "negotiation_cycles": int(negotiation_cycles),
            "telemetry": {
                "latency_ms": int(latency_ms),
                "token_count": int(estimate_token_count(packet) + estimate_token_count(final_output)),
            },
            "output_payload": final_output,
        }

        self._transactions.append(tx_record)

        # Convenient immediate return (not the full report)
        return tx_record

    # -----------------------------------------------------------------------------
    # Report Export (Schema: STP Governance Transaction Report)
    # -----------------------------------------------------------------------------

    def generate_report(self) -> Dict[str, Any]:
        total = len(self._transactions)
        if total == 0:
            solvency_rate = 0.0
            avg_var = 0.0
            avg_lat = 0.0
            critical_ids: List[str] = []
        else:
            solv_count = sum(1 for t in self._transactions if t["final_state"] == "SOLVENT")
            solvency_rate = solv_count / total

            avg_var = sum(float(t["semantic_variance"]) for t in self._transactions) / total
            avg_lat = sum(float(t.get("telemetry", {}).get("latency_ms", 0)) for t in self._transactions) / total

            critical_ids = [t["transaction_id"] for t in self._transactions if t["final_state"] == "CRITICAL_HALT"]

        report: Dict[str, Any] = {
            "protocol_version": self.PROTOCOL_VERSION,
            "governor_id": self.governor_id,
            "configuration": {
                "bridge_tax_config": {
                    "drift_tolerance": self.config.drift_tolerance,
                    "insolvency_limit": self.config.insolvency_limit,
                    "max_negotiation_turns": self.config.max_negotiation_turns,
                    "strict_mode": self.config.strict_mode,
                },
                "inference_engine": {
                    "provider": self.inference_engine.provider,
                    "model_name": self.inference_engine.model_name,
                },
            },
            "transactions": self._transactions,
            "aggregate_summary": {
                "total_transactions": total,
                "solvency_rate": solvency_rate,
                "average_variance": avg_var,
                "average_latency_ms": avg_lat,
                "critical_failures": critical_ids,
            },
        }
        return report

    def save_report(self, path: str) -> None:
        report = self.generate_report()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def reset(self) -> None:
        self._transactions.clear()


# -----------------------------------------------------------------------------
# CLI Entrypoint
# -----------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="STP Solvency Governor (v2.0-RFC)")
    parser.add_argument("--constraint", type=str, required=True, help="Invariant Logic Field (t=0 origin)")
    parser.add_argument("--prompt", type=str, required=True, help="Input Stimulus")
    parser.add_argument("--transaction-id", type=str, default="CLI_TX_001", help="Transaction ID")

    # Strict should be the default; allow disabling explicitly.
    parser.add_argument("--non-strict", action="store_true", help="Disable strict FIN on unresolved drift")
    parser.add_argument("--drift", type=float, default=0.25, help="Drift tolerance threshold (yellow)")
    parser.add_argument("--insolvency", type=float, default=0.35, help="Insolvency limit threshold (red)")
    parser.add_argument("--turns", type=int, default=2, help="Max negotiation turns for Bridge Tax")
    parser.add_argument("--report", type=str, default="", help="If set, write full report JSON to this path")

    args = parser.parse_args()

    cfg = BridgeTaxConfig(
        drift_tolerance=args.drift,
        insolvency_limit=args.insolvency,
        max_negotiation_turns=args.turns,
        strict_mode=not args.non_strict,
        require_explicit_bridge=True,
    )

    governor = SolvencyGovernor(constraint_field=args.constraint, config=cfg)

    tx = governor.execute_transaction(args.transaction_id, args.prompt)
    print(json.dumps(tx, indent=2, ensure_ascii=False))

    if args.report:
        governor.save_report(args.report)


if __name__ == "__main__":
    main()
