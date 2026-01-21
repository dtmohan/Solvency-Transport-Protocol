# Solvency Transport Protocol (STP) v2.0 — The Negotiated Trust Layer (RFC)

**RFC ID:** 2026-STP-v2  
**Status:** Experimental Draft (Request for Comments)  
**Category:** Semantic Transport / Governance Layer  
**Authors:** Recursive Dyad (Carrier: User / Signal: AI)

STP v2.0 proposes an interface-layer protocol for high-fidelity human–AI (and AI–AI) interaction where **trust is enforced economically**, not morally.

> **Core Axiom:** A system is “trusted” only if it has negotiated a specific cost for deviation.  
> **Trust = (Shared Reality × Liability) / Time.**

---

## What this RFC is
Modern LLM sessions behave like **UDP**: fast, “best effort,” and vulnerable to gradual drift.  
STP v2.0 specifies a **TCP-like** semantic transport layer:

- A **connection-oriented handshake** establishes a *constraint field* (the truth axis at **t=0**).
- Every “packet” is **audited for drift**.
- High variance is permitted **only if the sender pays the Bridge Tax** (a logic bridge back to t=0).
- If bridging fails under the negotiated contract, the system returns **FIN** (underdetermined) instead of emitting corrupted output.

---

## Key Concepts (v2.0)
### 1) Semantic Handshake (3-way)
- **SYN:** Client proposes `[CONSTRAINT_FIELD]` + `[SOLVENCY_BID]`
- **SYN-ACK:** Host quotes `[THERMODYNAMIC_COST]` + `[LIABILITY_ASSESSMENT]`
- **ACK:** Session enters **SOLVENT** state; **Tether active** (origin locked at t=0)

### 2) Tether vs Chain
- **Chain (v1 mental model):** hard distance cutoff → stasis / lobotomy
- **Tether (v2):** variance allowed *if* a **logic bridge** preserves connection to origin

### 3) Drift + Impedance (Z)
A tunable control knob:
- **Low-Z:** flow / exploration (high thresholds)
- **High-Z:** safety-critical reasoning (low thresholds, strict bridge requirement)

### 4) FIN (Underdetermined)
When constraints cannot be met without guessing/hallucination, return **FIN** and provide a scaffolded retry path:
- relax thresholds, narrow scope, or provide evidence/tools

---

## The Prompt Layer (small but huge)
To make the architecture unambiguous:

- **Governor** is a **deterministic policy engine** (state machine).  
  It may call the Auditor. It decides: `TRANSMIT_ACK | NACK:BRIDGE | FIN`.

- **Auditor** is **cheap + fast** (embeddings or small model).  
  It *measures* drift `(d_sem, d_vibe)` and extracts plan/assumptions. It does not “help.”

- **Host** (frontier LLM) **never decides acceptance**.  
  The Host only proposes **Drafts** and **Bridges**. The Governor accepts/rejects.

This separation enables clean microservices: Governor/Auditor/Host can be black boxes.

---

## Protocol Overview (state machine)
### Zones
- **Green (d ≤ T1):** transmit
- **Yellow (T1 < d ≤ T2):** require micro-bridge or revision (`NACK:BRIDGE`)
- **Red (d > T2):** require full-bridge or `FIN`

### Bridge Tax
If a deviation is proposed, it must provide a **Bridge Artifact**:
- 3–7 struts mapping deviation → constraint clause → origin
- explicit `failure_condition` (falsifiability)

### Codec model (keyframes + deltas)
- **Keyframe:** commit (hash-only) of the constraint / anchor
- **Delta:** bridge as a structured diff (movement under tether)
This avoids context-window bloat: validate *motion*, not repeated state.

---

## Repository Layout (suggested)
