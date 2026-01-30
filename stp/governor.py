#!/usr/bin/env python3
"""
Solvency Transport Protocol (STP) - v2.0-RFC Kernel
Deterministic Governance and Recursive Solvency Enforcement.
"""

import json
import hashlib
import time
import uuid
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional

class SolvencyZone(Enum):
    GREEN = auto()    # Resonant: Within T1
    YELLOW = auto()   # Dissonant: T1 < d <= T2 (Bridge Required)
    RED = auto()      # Decoupled: d > T2 (Critical Halt)

class STPKernel:
    """
    The Governor: Enforces the Thermodynamics of Drift through a 
    deterministic state machine and cryptographic ledger.
    """
    def __init__(self, config_path: str, auditor):
        # Load deployment configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Protocol Metadata
        self.governor_id = self.config.get("governor_id", "stp-kernel-001")
        self.c = self.config["configuration"]["primary_invariant"]
        self.c_hash = hashlib.sha256(self.c.encode()).hexdigest()
        self.nonce = uuid.uuid4().hex
        
        # Internal Parameters
        self.auditor = auditor
        self.t1 = self.config["configuration"]["bridge_tax_config"]["drift_tolerance"]
        self.t2 = self.config["configuration"]["bridge_tax_config"]["insolvency_limit"]
        self.l_rate = self.config["configuration"]["bridge_tax_config"].get("return_policy", {}).get("lambda", 0.25)
        
        # State & Ledger
        self.prev_commit = "0" * 64
        self.ledger = []
        self.transactions = []
        self.start_time = time.time()
        
        self.anchor_session()

    def canonical_hash(self, data: Dict) -> str:
        """RFC Requirement: Canonical JSON for commit determinism."""
        c_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(c_json.encode()).hexdigest()

    def _emit_frame(self, frame_type: str, payload: Dict) -> str:
        """Encodes interaction as delta frames in the helical ledger."""
        frame = {
            "frame_type": frame_type,
            "epoch": int(time.time()),
            "origin_ref": {
                "constraint_hash": self.c_hash,
                "session_nonce": self.nonce
            },
            "prev_commit": self.prev_commit,
            "payload": payload
        }
        commit = self.canonical_hash(frame)
        frame["delta_commit"] = commit
        self.prev_commit = commit
        self.ledger.append(frame)
        return commit

    def anchor_session(self):
        """Initial KEYFRAME_COMMIT (t=0)."""
        self._emit_frame("KEYFRAME_COMMIT", {"c": self.c})

    def process_turn(self, candidate_output: str, tx_id: str) -> Tuple[SolvencyZone, str]:
        """
        Main Governance Loop:
        1. Calculate drift (max of d_sem and d_vibe).
        2. Arbitrate Solvency Zone.
        3. Record telemetry for Schema compliance.
        """
        d_sem, d_vibe = self.auditor.compute_drift(self.c, candidate_output)
        d = max(d_sem, d_vibe)

        if d <= self.t1:
            zone = SolvencyZone.GREEN
            state = "SOLVENT"
            msg = "TRANSMIT_ACK"
            self.apply_phased_return(d)
        elif d <= self.t2:
            zone = SolvencyZone.YELLOW
            state = "DRIFT_DETECTED"
            msg = "NACK:BRIDGE_REQUIRED"
        else:
            zone = SolvencyZone.RED
            state = "CRITICAL_HALT"
            msg = "FIN:UNDERDETERMINED"

        # Record transaction telemetry for the 2020-12 Schema report
        self.transactions.append({
            "transaction_id": tx_id,
            "timestamp_ms": int(time.time() * 1000),
            "final_state": state,
            "semantic_variance": round(d, 4),
            "bridge_tax_paid": False,  # Updated if verify_bridge passes
            "negotiation_cycles": 0,
            "output_payload": candidate_output
        })
        
        return zone, msg

    def verify_bridge(self, bridge_artifact: Dict) -> bool:
        """Structural Verification of the Bridge Tax."""
        ref = bridge_artifact.get("origin_ref", {})
        if ref.get("session_nonce") != self.nonce:
            return False
        
        struts = bridge_artifact.get("struts", [])
        if not (3 <= len(struts) <= 7):
            return False
            
        if "failure_condition" not in bridge_artifact or "constraint_clause" not in bridge_artifact:
            return False
            
        # Log successful reconciliation
        self._emit_frame("DELTA_BRIDGE", bridge_artifact)
        if self.transactions:
            self.transactions[-1]["bridge_tax_paid"] = True
            self.transactions[-1]["negotiation_cycles"] += 1
            
        return True

    def apply_phased_return(self, current_variance: float):
        """S_{t+1} <- (1-lambda)S_t + lambda*V0."""
        payload = {
            "return_step": {"lambda": self.l_rate, "target": "origin"},
            "drift": {"d": current_variance}
        }
        return self._emit_frame("DELTA_RETURN", payload)

    def save_report(self, output_path: str):
        """Generates the STP Governance Transaction Report."""
        total = len(self.transactions)
        solvent_count = sum(1 for tx in self.transactions if tx["final_state"] == "SOLVENT")
        failures = [tx["transaction_id"] for tx in self.transactions if tx["final_state"] == "CRITICAL_HALT"]
        
        report = {
            "protocol_version": "2.0-RFC",
            "governor_id": self.governor_id,
            "configuration": self.config["configuration"],
            "transactions": self.transactions,
            "aggregate_summary": {
                "total_transactions": total,
                "solvency_rate": (solvent_count / total) * 100 if total > 0 else 0,
                "average_latency_ms": (time.time() - self.start_time) * 1000 / total if total > 0 else 0,
                "critical_failures": failures
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
