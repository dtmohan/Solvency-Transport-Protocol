#!/usr/bin/env python3
"""
Solvency Transport Protocol (STP) - v2.0-RFC Kernel
Enforces Negotiated Governance and Recursive Solvency.
"""

import json
import hashlib
import time
import uuid
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from auditor import InternalEarAuditor # Integrated Auditor Handle [cite: 80, 81]

class SolvencyZone(Enum):
    GREEN = auto()    # Resonant [cite: 214]
    YELLOW = auto()   # Dissonant [cite: 215]
    RED = auto()      # Decoupled [cite: 216]
    CRITICAL = auto() # FIN/Abort [cite: 11]

class STPKernel:
    """
    The Governor: A deterministic policy engine and state machine[cite: 80].
    """
    def __init__(self, constraint: str, auditor: InternalEarAuditor, t1=0.05, t2=0.15, l_rate=0.25):
        self.c = constraint
        self.c_hash = hashlib.sha256(constraint.encode()).hexdigest() [cite: 156]
        self.nonce = uuid.uuid4().hex [cite: 157]
        self.auditor = auditor
        self.t1 = t1 
        self.t2 = t2 
        self.l_rate = l_rate # Negotiated return rate lambda [cite: 102]
        
        self.prev_commit = "0" * 64 [cite: 159]
        self.ledger = []
        self.anchor_session()

    def canonical_hash(self, data: Dict) -> str:
        """RFC Requirement: Canonical JSON for commit determinism."""
        c_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(c_json.encode()).hexdigest()

    def _emit_frame(self, frame_type: str, payload: Dict) -> str:
        """Encodes interaction as delta frames between keyframes[cite: 128]."""
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
        commit = self.canonical_hash(frame) [cite: 161]
        frame["delta_commit"] = commit
        self.prev_commit = commit
        self.ledger.append(frame)
        return commit

    def anchor_session(self):
        """Initial KEYFRAME_COMMIT (t=0)[cite: 129, 131]."""
        self._emit_frame("KEYFRAME_COMMIT", {"c": self.c})

    def process_turn(self, candidate_output: str) -> Tuple[SolvencyZone, str]:
        """
        Executes the main Governance loop[cite: 121].
        1. Drift Check (Auditor)
        2. Zone Arbitration (Governor)
        3. Phased Return (Helical State)
        """
        # 1. Audit [cite: 107]
        d_sem, d_vibe = self.auditor.compute_drift(self.c, candidate_output) [cite: 220]
        d = max(d_sem, d_vibe) [cite: 90, 210]

        # 2. Zone Arbitration [cite: 91, 92, 93]
        if d <= self.t1:
            zone = SolvencyZone.GREEN
            self.apply_phased_return(d)
            return zone, "TRANSMIT_ACK" [cite: 80, 112]
        
        elif d <= self.t2:
            zone = SolvencyZone.YELLOW
            return zone, "NACK:BRIDGE_REQUIRED" [cite: 80, 116]
        
        else:
            zone = SolvencyZone.RED
            # High variance requires full Bridge Artifact or FIN [cite: 93]
            return zone, "FIN:UNDERDETERMINED" [cite: 11, 114]

    def verify_bridge(self, bridge_artifact: Dict) -> bool:
        """
        Structural Verification Function[cite: 193, 194].
        1. Anchor Rule: Match hash(C) and session nonce[cite: 195].
        2. Form Rule: 3-7 ordered struts + failure condition[cite: 196].
        3. Scope Rule: Restate constraint_clause[cite: 197].
        """
        ref = bridge_artifact.get("origin_ref", {})
        if ref.get("session_nonce") != self.nonce:
            return False
        
        struts = bridge_artifact.get("struts", [])
        if not (3 <= len(struts) <= 7):
            return False
            
        if "failure_condition" not in bridge_artifact or "constraint_clause" not in bridge_artifact:
            return False
            
        self._emit_frame("DELTA_BRIDGE", bridge_artifact) [cite: 244]
        return True

    def apply_phased_return(self, current_variance: float):
        """S_{t+1} <- (1-l)S_t + l*V0[cite: 101, 120]."""
        payload = {
            "return_step": {"lambda": self.l_rate, "target": "origin"},
            "drift": {"d": current_variance}
        }
        return self._emit_frame("DELTA_RETURN", payload) [cite: 245]
