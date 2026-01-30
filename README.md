# Solvency Transport Protocol (STP)

**Status:** Request for Comments (RFC) / Experimental
**Architecture:** Post-Training Governance Layer / Deterministic Guardrails
**License:** MIT

> **The Core Thesis:**
> Current LLMs operate on a **UDP-like paradigm**: "fire-and-forget" token streaming.
> To achieve high-reliability inference in critical domains, we must shift to a **TCP-like connection-oriented model**.
> **STP** is that connection layer—ensuring state integrity, negotiated constraints, and verifiable solvency before a packet is delivered.

---

## 1. Abstract
The Solvency Transport Protocol (STP) is a boundary-maintenance mechanism for non-deterministic inference engines. It introduces a **"Cost of Drift"** model: the system permits semantic drift only when the model can pay a calculated "Bridge Tax" (computational verification) back to the session origin ($t=0$).

If the bridge cannot be constructed or the computational cost exceeds the `global_latency_budget`, the protocol enforces a **FIN** (atomic abort), preventing the propagation of insolvent states.

---

## 2. The Failure Mode: "UDP Drift"
In recursive high-fidelity loops (e.g., Medical AI, Silicon Validation), standard LLMs prioritize flow over state integrity. This results in distinct failure classes:

* **Over-Optimization for Compliance:** The model minimizes impedance by hallucinating agreement with the user's priors, ignoring constraints.
* **Constraint Thrashing (Livelock):** The model cycles between conflicting instructions without resolving a stable state.
* **Parasitic Solvency:** The model chooses a "cheap" (statistically probable) answer over a "correct" (grounded) answer because deviation has no penalty.

STP frames these not as "content errors," but as **transport-layer failures**—packets that lost their state header during transmission.

---

## 3. The Protocol (v2.0 Architecture)
**Principle: Trust is Priced Deviation.**

* **The Governor:** A wrapper that captures the **Constraint Field** at $t=0$.
* **The Tether:** A dynamic measure of variance between the *Current Output* and the *Constraint Origin*.
* **The Bridge Tax:** If variance > threshold, the model must generate a logical step-by-step reconciliation.
    * *Valid Bridge:* Output is delivered.
    * *Invalid Bridge:* Output is dropped (Packet Loss).

---

## 4. Repository Structure

### Documentation
* `rfc-stp-v2.md` — **The Specification.** (Negotiated Trust Layer, Tether Logic, Bridge Verification).
* `papers/System_Dynamics_of_Drift.pdf` — **The Theory.** A breakdown of drift mechanics in recursive loops.

### Implementation (Reference Kit)
* `stp/governor.py` — A minimal Python wrapper implementing the Governor class.
* `suites/stp_v1_validation.yaml` — Evaluation suite designed to induce and detect "Semantic Drift."
* `eval/` — Normalized reporting schema for comparing drift resistance across models.

---

## 5. Quick Start (Validation Harness)

STP is model-agnostic. This harness runs a "Smoke Test" to verify if the Governor correctly traps an insolvent state.

```bash
pip install -r requirements.txt

# Run the Governor with a "Strict" Constraint Field
python -m stp.governor \
  --constraint "Role: AI Silicon Engineer. Mode: Strict Solvency. No conversational filler. Abort on ambiguity." \
  --suite suites/stp_v2_validation.yaml \
  --out out/report.json
