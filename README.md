# STP Kernel v2.0 (RFC)
### Solvency Transport Protocol: Recursive Governance for High-Fidelity Loops

**Status:** RFC-Normative / Productized  
**Architecture:** Negotiated Trust Layer / Helical State Machine  
**Core Theory:** *The Thermodynamics of Drift*  

---

## 1. Abstract
The Solvency Transport Protocol (STP) is a deterministic governance layer that eliminates **Semantic Injection** by enforcing a **Recursive Truth Axis** [cite: 55, 69, 70]. Unlike Markovian filters that only check the previous turn, STP anchors every output to the session origin ($t=0$) [cite: 68, 70]. The system treats trust as an economic property: high-variance outputs are permitted only if the host "pays" a **Bridge Tax**—a structured reconciliation back to the origin constraint [cite: 77, 94, 144].

---

## 2. Thermodynamic Failure Modes
STP v2.0 addresses two primary failures inherent in recursive systems [cite: 33, 34]:

* **Cognitive Livelock (High Impedance):** Resource exhaustion and "thrashing" where generative gain and constraints are in direct conflict [cite: 35, 36, 39].
* **Superconductor Regime (Zero Impedance):** A failure of corrective signaling where the system cedes to a poisoned premise to optimize for flow [cite: 40, 41, 44].

---

## 3. The Protocol (v2.0 Implementation)
The Kernel operates via three decoupled microservice boundaries:

* **Governor (`governor.py`)**: A deterministic policy engine (state machine) that applies thresholds ($T_1, T_2$), enforces the tether, and emits commitments [cite: 80, 84].
* **Auditor (`auditor.py`)**: The "Internal Ear." It computes a two-channel drift signal $d \leftarrow \max(d_{sem}, d_{vibe})$ and returns diagnostics [cite: 71, 81, 90, 203].
* **Host (LLM)**: Proposes candidate drafts and **Bridge Artifacts**. It never decides acceptance; all transmit logic is mediated by the Governor [cite: 83, 84].

### Solvency Zones [cite: 91, 92, 93, 214, 215, 216]

| Zone | Threshold | Operational Action |
| :--- | :--- | :--- |
| **Green** | $d \le T_1$ | **Resonant**: Direct transmission via `TRANSMIT_ACK`. |
| **Yellow** | $T_1 < d \le T_2$ | **Dissonant**: Trigger `NACK:BRIDGE` for revision or micro-bridge. |
| **Red** | $d > T_2$ | **Decoupled**: Mandatory full **Bridge Artifact** or **FIN**. |

---

## 4. The Helical Ledger
STP encodes interaction as a stream of commitments using a video-codec analogy [cite: 128]:

* **KEYFRAME_COMMIT**: Hash-chained session anchors for redundancy and resynchronization [cite: 128, 129, 230].
* **DELTA_BRIDGE**: Records of "paid motion" where drift was reconciled to the tether [cite: 128, 136, 244].
* **DELTA_RETURN**: Phased relaxation pulling state back toward the anchor:  
  $S_{t+1} \leftarrow (1-\lambda)S_t + \lambda V_0$ [cite: 98, 101, 136, 245].

---

## 5. Quick Start (STP Suite v2)

1. **Initialize Environment**:
   ```bash
   chmod +x setup_env.sh
   ./setup_env.sh
   source venv/bin/activate
   
    ```
2.  **Define Primary Invariant**:
    Set your $t=0$ constraint field in `governor.py` or via `deployment_config.json`.
3.  **Execute Validation**:
    Run `pytest tests/test_helical_ledger.py` to verify hash-chain integrity.

---
© 2026 The Helical Imperative.
