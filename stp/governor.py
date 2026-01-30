#!/usr/bin/env python3
"""
Solvency Transport Protocol (STP) - v2.0-RFC Kernel
"""

import json
import hashlib
import time
import uuid
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from auditor import InternalEarAuditor

class SolvencyZone(Enum):
    GREEN = auto()    
    YELLOW = auto()   
    RED = auto()      
    CRITICAL = auto() 

class STPKernel:
    def __init__(self, constraint: str, auditor: InternalEarAuditor, t1=0.05, t2=0.15, l_rate=0.25):
        self.c = constraint
        self.c_hash = hashlib.sha256(constraint.encode()).hexdigest()
        self.nonce = uuid.uuid4().hex
        self.auditor = auditor
        self.t1 = t1 
        self.t2 = t2 
        self.l_rate = l_rate 
        
        self.prev_commit = "0" * 64
        self.ledger = []
        self.anchor_session()

    def canonical_hash(self, data: Dict) -> str:
        c_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(c_json.encode()).hexdigest()

    def _emit_frame(self, frame_type: str, payload: Dict) -> str:
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
        self._emit_frame("KEYFRAME_COMMIT", {"c": self.c})

    def process_turn(self, candidate_output: str) -> Tuple[SolvencyZone, str]:
        d_sem, d_vibe = self.auditor.compute_drift(self.c, candidate_output)
        d = max(d_sem, d_vibe)

        if d <= self.t1:
            self.apply_phased_return(d)
            return SolvencyZone.GREEN, "TRANSMIT_ACK"
        elif d <= self.t2:
            return SolvencyZone.YELLOW, "NACK:BRIDGE_REQUIRED"
        else:
            return SolvencyZone.RED, "FIN:UNDERDETERMINED"

    def verify_bridge(self, bridge_artifact: Dict) -> bool:
        ref = bridge_artifact.get("origin_ref", {})
        if ref.get("session_nonce") != self.nonce:
            return False
        
        struts = bridge_artifact.get("struts", [])
        if not (3 <= len(struts) <= 7):
            return False
            
        if "failure_condition" not in bridge_artifact or "constraint_clause" not in bridge_artifact:
            return False
            
        self._emit_frame("DELTA_BRIDGE", bridge_artifact)
        return True

    def apply_phased_return(self, current_variance: float):
        payload = {
            "return_step": {"lambda": self.l_rate, "target": "origin"},
            "drift": {"d": current_variance}
        }
        return self._emit_frame("DELTA_RETURN", payload)
