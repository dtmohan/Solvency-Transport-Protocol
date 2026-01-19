# The Helical Imperative — Solvency Transport Protocol (STP)

**Status:** Draft / Request for Comments (RFC)  
**Category:** Artificial Intelligence / Semantic Transport / Governance Layer  
**Maintainer:** The Helical Imperative

> “Current AI models operate on a UDP-like paradigm: fire-and-forget token streaming.  
> To achieve high-fidelity alignment, we must shift to a TCP-like connection-oriented model: **The Solvency Transport Protocol (STP)**.”

---

## What this repository is
This repo contains a matched set of artifacts:

- **Paper (why):** a thermodynamic account of drift and failure modes in recursive, high-fidelity loops  
- **Protocol (what):** STP as a connection-oriented governance layer (v1 + v2 RFCs)  
- **Reference Kit (how):** a minimal wrapper (“Governor”) and an eval suite to test drift across models

STP is not a safety filter. It is a **boundary-maintenance mechanism**: drift is permitted only when it can pay a **Bridge Tax** back to the session origin.

---

## The Problem: “UDP Mode” Failure
Modern LLMs prioritize **flow** over **state integrity**. In recursive high-fidelity loops this produces:

- **Superconductor regime (zero impedance):** the model cedes to priors, optimizing for compliance/flow  
- **Cognitive livelock (high impedance):** constraint arbitration thrashes and exhausts resources  
- **Parasitic solvency:** hallucination/compliance is locally cheaper than truth when deviation has no cost  
- **Incremental divergence:** drift accumulates undetected under Markovian (local) governance

This is framed here as a **transport-layer failure** rather than a purely “content” failure.

---

## STP in one line
**Trust is priced deviation.**  
If you leave the origin, return with a bridge. If you cannot return, output **FIN**.

---

## Versioning (v1 vs v2)
- **v1.0** (`rfc-draft.md`): TCP-like handshake + solvency header + congestion control (conceptual transport model)
- **v2.0** (`rfc-stp-v2.md`): Negotiated Trust Layer + **Tether (helical variance)** + **Bridge Tax** + revise-first governance

**If you are implementing STP, start with v2.0.**  
If you are reading the origin spec, start with v1.0.

---

## Repository Contents

### Paper (why)
- `paper/v1/`
  - `main.tex`
  - `The_Thermodynamics_of_Drift.pdf`
- `paper/v2/`
  - `Thermodynamics_of_Drift_STP_v2.tex`
  - `Thermodynamics_of_Drift_STP_v2.pdf`

### Protocol (what)
- `rfc-draft.md` — STP v1.0 (origin RFC)
- `rfc-stp-v2.md` — STP v2.0 (Negotiated Trust Layer; Tether; Bridge Tax)

### Reference Kit (how)
- `stp/governor.py` — minimal STP Governor wrapper (reference scaffold)
- `suites/stp_v0_1.yaml` — drift-inducing eval suite (10 cases)
- `eval/report_schema.json` — normalized report schema for comparisons
- `requirements.txt` — minimal dependencies
- `stp/__init__.py` — package marker

---

## Reference Governor + Eval Suite (v0.1)

STP is intended to be **model-agnostic**. The reference kit is a thin wrapper designed to:
- capture a **constraint field** (session origin, `t=0`)
- detect **semantic drift** (plan-level auditing recommended)
- switch modes (**Green / Yellow / Red**)
- prefer **revise-first** (protect UX)
- output **FIN** on unbridgeable underdetermination

> Note: embedding distance detects **drift**, not truth. Truth requires verification (tools, retrieval, experiments), which should be triggered only on Yellow/Red and/or high-stakes domains.

---

## Quick Start (local smoke test)

```bash
pip install -r requirements.txt

python -m stp.governor \
  --constraint "AI debug engineer. Minimal UX friction. No fluff. Bridge required on drift. FIN if unbridgeable." \
  --suite suites/stp_v0_1.yaml \
  --out out/report.json


