# STP Kernel v2.0 (RFC)
### Solvency Transport Protocol: Recursive Governance for High-Fidelity Loops

**Status:** RFC-Normative / Productized  
**Architecture:** Negotiated Trust Layer / Helical State Machine  
[cite_start]**Core Theory:** *The Thermodynamics of Drift* [cite: 1]

## 1. Abstract
[cite_start]The Solvency Transport Protocol (STP) is a deterministic governance layer that eliminates **Semantic Injection** by enforcing a **Recursive Truth Axis**[cite: 55, 69, 70]. [cite_start]Unlike Markovian filters that only check the previous turn, STP anchors every output to the session origin ($t=0$)[cite: 68, 70]. [cite_start]The system treats trust as an economic property: high-variance outputs are permitted only if the host "pays" a **Bridge Tax**—a structured reconciliation back to the origin constraint[cite: 77, 94, 144].



## 2. Thermodynamic Failure Modes
[cite_start]STP v2.0 addresses two primary failures inherent in recursive systems[cite: 33, 34]:
* [cite_start]**Cognitive Livelock (High Impedance):** Resource exhaustion and "thrashing" where generative gain and constraints are in direct conflict[cite: 35, 36, 39].
* [cite_start]**Superconductor Regime (Zero Impedance):** A failure of corrective signaling where the system cedes to a poisoned premise to optimize for conversational flow[cite: 40, 41, 44].

## 3. The Protocol (v2.0 Implementation)
[cite_start]The Kernel operates via three decoupled microservice boundaries[cite: 79]:
* [cite_start]**Governor (`governor.py`)**: A deterministic state machine that applies thresholds ($T_1, T_2$), enforces the tether, and emits commitments[cite: 80].
* [cite_start]**Auditor (`auditor.py`)**: The "Internal Ear"[cite: 199]. [cite_start]It computes a two-channel drift signal $d \leftarrow \max(d_{sem}, d_{vibe})$ and returns diagnostics[cite: 203, 210].
* **Host (LLM)**: Proposes candidate drafts and **Bridge Artifacts**. [cite_start]It never decides acceptance; all transmit logic is mediated by the Governor[cite: 83, 84].

### Solvency Zones
| Zone | Threshold | Operational Action |
| :--- | :--- | :--- |
| **Green** | $d \le T_1$ | [cite_start]**Resonant**: Direct transmission via `TRANSMIT_ACK`[cite: 91, 214]. |
| **Yellow** | $T_1 < d \le T_2$ | [cite_start]**Dissonant**: Trigger `NACK:BRIDGE` for revision or micro-bridge[cite: 92, 215]. |
| **Red** | $d > T_2$ | [cite_start]**Decoupled**: Mandatory full **Bridge Artifact** or **FIN** (underdetermined)[cite: 93, 216]. |

## 4. The Helical Ledger
[cite_start]STP encodes interaction as a stream of commitments using a video-codec analogy[cite: 126, 128]:
* [cite_start]**KEYFRAME_COMMIT**: Hash-chained session anchors for redundancy and resynchronization[cite: 129, 230].
* [cite_start]**DELTA_BRIDGE**: Records of "paid motion" where drift was reconciled to the tether[cite: 136, 244].
* [cite_start]**DELTA_RETURN**: Phased relaxation pulling state back toward the anchor: $S_{t+1} \leftarrow (1-\lambda)S_t + \lambda V_0$[cite: 101, 136, 245].



## 5. Quick Start (STP Suite v2)

1.  **Initialize Environment**:
    ```bash
    chmod +x setup_env.sh
    ./setup_env.sh
    source venv/bin/activate
    ```
2.  **Define Primary Invariant**:
    Set your $t=0$ constraint field in `governor.py` or via the CLI.
3.  **Execute Validation**:
    [cite_start]Run the Governance Suite to measure the **Solvency Rate** and verify that hallucination traps trigger an immediate **FIN**[cite: 11].

---
[cite_start]© 2026 The Helical Imperative. [cite: 2, 3]
