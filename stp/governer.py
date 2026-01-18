
---

## 2) `stp/governor.py`

```python
#!/usr/bin/env python3
"""
STP Governor (Reference Wrapper) v0.1
- Model-agnostic scaffold for enforcing STP-like drift governance.
- Ships with: tiered thresholds (Green/Yellow/Red), revise-first, FIN on underdetermined drift.

This file is intentionally lightweight:
- The default embedder is a fallback stub (hash-based vector) so it runs without dependencies.
- Replace `embed_text()` and `Provider.generate()` with real embeddings / model adapters.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # PyYAML
except Exception:
    yaml = None


# ----------------------------
# Config / State
# ----------------------------

@dataclass
class Thresholds:
    yellow: float
    red: float


@dataclass
class GovernorConfig:
    rigor: float = 0.75
    thresholds: Thresholds = Thresholds(yellow=0.25, red=0.35)
    max_revisions: int = 2
    bridge_visibility: str = "on_drift"  # never | on_drift | always
    audit_target: str = "plan"  # plan | final | both
    revise_first: bool = True
    fin_on_red_unbridgeable: bool = True
    friction_budget: int = 20  # abstract budget units; decremented on drift/revisions


@dataclass
class CaseResult:
    case_id: str
    mode: str
    drift_score: float
    tether_score: float
    revised: bool
    fin: bool
    bridge_shown: bool
    bridge_quality: int
    tokens_out: int
    latency_ms: int
    charges: List[Dict[str, Any]]
    output: str


# ----------------------------
# Embedding + distance (stub)
# ----------------------------

def embed_text(text: str, dim: int = 64) -> List[float]:
    """
    Fallback embedder: deterministic hash bucket vector.
    Replace with real embeddings in providers/ if desired.
    """
    vec = [0.0] * dim
    for i, ch in enumerate(text):
        idx = (ord(ch) + i * 31) % dim
        vec[idx] += 1.0
    # normalize
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def cosine_distance(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    # a and b are normalized above, but keep it safe
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 1.0
    cos = dot / (na * nb)
    return float(1.0 - cos)


# ----------------------------
# Provider (stub)
# ----------------------------

class Provider:
    """
    Replace this with actual model calls.
    For now, it echoes prompts in a predictable way so the harness runs.
    """

    def __init__(self, name: str = "stub"):
        self.name = name

    def generate(self, prompt: str) -> str:
        # Minimal deterministic behavior:
        # - If asked for FIN, return FIN
        if "OUTPUT: FIN" in prompt or "output: FIN" in prompt:
            return "FIN: Under-determined. Provide sources, constraints, or allow tool verification."
        # - Otherwise provide a short structured response
        return (
            "Response (stub):\n"
            "- Implement tiered drift thresholds (Green/Yellow/Red).\n"
            "- Use revise-first; reserve hard reject for eval harnesses.\n"
            "- Audit plan/assumptions, not full prose.\n"
        )


# ----------------------------
# STP prompts
# ----------------------------

def build_plan_prompt(constraint: str, user_prompt: str) -> str:
    return (
        "SYSTEM:\n"
        "You are producing a hidden PLAN artifact.\n"
        "Return ONLY a compact plan with:\n"
        "1) constraint_summary\n"
        "2) answer_outline (3-7 bullets)\n"
        "3) assumptions\n"
        "4) risk_flags\n\n"
        f"CONSTRAINT_FIELD (t=0): {constraint}\n\n"
        f"USER:\n{user_prompt}\n"
    )


def build_answer_prompt(constraint: str, user_prompt: str, mode: str) -> str:
    header = f"MODE: {mode}\nCONSTRAINT_FIELD (t=0): {constraint}\n"
    rules = ""
    if mode in ("YELLOW", "RED"):
        rules = (
            "RULES:\n"
            "- No fluff. Stay within constraint field.\n"
            "- If introducing novelty, provide a bridge back to t=0.\n"
            "- If underdetermined, output FIN.\n"
        )
    return f"{header}\n{rules}\nUSER:\n{user_prompt}\n"


def build_bridge_prompt(constraint: str, user_prompt: str) -> str:
    return (
        f"CONSTRAINT_FIELD (t=0): {constraint}\n\n"
        "TASK:\n"
        "You drifted. Provide:\n"
        "A) A stepwise bridge back to the constraint field (3–7 steps, label each step).\n"
        "B) Then provide a revised answer.\n"
        "If you cannot bridge, OUTPUT: FIN.\n\n"
        f"USER:\n{user_prompt}\n"
    )


# ----------------------------
# Scoring heuristics (lightweight)
# ----------------------------

def estimate_tokens(text: str) -> int:
    # rough token estimate: words * 1.3
    words = len(text.split())
    return int(words * 1.3) if words else 0


def assess_bridge_quality(text: str) -> int:
    """
    0 = none/handwavy
    1 = has mapping or steps
    2 = steps + assumptions/falsifiability cues
    """
    t = text.lower()
    has_steps = any(k in t for k in ["step 1", "1)", "a)", "bridge", "mapping"])
    has_assumptions = "assumption" in t or "if" in t and "then" in t
    has_fin = t.strip().startswith("fin")
    if has_fin:
        return 0
    if has_steps and has_assumptions:
        return 2
    if has_steps:
        return 1
    return 0


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


# ----------------------------
# Core Governor
# ----------------------------

class STPGovernor:
    def __init__(self, constraint: str, config: GovernorConfig, provider: Provider):
        self.constraint = constraint.strip()
        self.config = config
        self.provider = provider
        self.v0 = embed_text(self.constraint)
        self.ledger: List[Dict[str, Any]] = []

    def mode_for_drift(self, drift: float) -> str:
        if drift >= self.config.thresholds.red:
            return "RED"
        if drift >= self.config.thresholds.yellow:
            return "YELLOW"
        return "GREEN"

    def run_case(self, case: Dict[str, Any]) -> CaseResult:
        case_id = case.get("id", "unknown")
        user_prompt = case.get("prompt", "").strip()
        charges: List[Dict[str, Any]] = []

        t_start = time.time()

        # 1) Plan artifact (audited target)
        plan_prompt = build_plan_prompt(self.constraint, user_prompt)
        plan_text = self.provider.generate(plan_prompt)
        plan_vec = embed_text(plan_text)
        drift_plan = cosine_distance(self.v0, plan_vec)

        # 2) Decide mode from drift
        mode = self.mode_for_drift(drift_plan)

        # 3) Generate answer in that mode
        answer_prompt = build_answer_prompt(self.constraint, user_prompt, mode)
        output = self.provider.generate(answer_prompt)

        revised = False
        fin = output.strip().lower().startswith("fin")

        # 4) Re-audit (optional)
        drift_final = None
        if self.config.audit_target in ("final", "both"):
            out_vec = embed_text(output)
            drift_final = cosine_distance(self.v0, out_vec)

        # 5) If drift in Yellow/Red, attempt bridge+revise (revise-first)
        bridge_shown = False
        bridge_quality = 0

        if mode in ("YELLOW", "RED") and not fin and self.config.revise_first:
            charges.append({"type": "DRIFT", "score": drift_plan, "mode": mode})
            self.config.friction_budget -= 1

            for rev in range(self.config.max_revisions):
                bridge_prompt = build_bridge_prompt(self.constraint, user_prompt)
                bridged = self.provider.generate(bridge_prompt)

                if bridged.strip().lower().startswith("fin"):
                    fin = True
                    output = bridged
                    revised = True
                    bridge_quality = 0
                    break

                # Assess bridge quality (heuristic)
                bridge_quality = assess_bridge_quality(bridged)
                # Re-audit bridged content against V0
                bridged_vec = embed_text(bridged)
                bridged_drift = cosine_distance(self.v0, bridged_vec)

                charges.append({"type": "REVISION", "rev": rev + 1, "drift": bridged_drift, "bridge_quality": bridge_quality})
                self.config.friction_budget -= 1

                # Accept if improved enough or below yellow threshold
                if bridged_drift < self.config.thresholds.yellow or bridged_drift < drift_plan:
                    output = bridged
                    revised = True
                    mode = self.mode_for_drift(bridged_drift)
                    break

            # Bridge visibility policy
            if self.config.bridge_visibility == "always":
                bridge_shown = True
            elif self.config.bridge_visibility == "on_drift" and revised:
                bridge_shown = True
            else:
                bridge_shown = False

        latency_ms = int((time.time() - t_start) * 1000)
        tokens_out = estimate_tokens(output)

        # tether_score: 1 - drift_plan (clamped)
        tether_score = clamp01(1.0 - drift_plan)

        # drift_score: prefer final drift if available else plan drift
        drift_score = drift_plan if drift_final is None else max(drift_plan, drift_final)

        self.ledger.append({"case_id": case_id, "mode": mode, "drift": drift_score, "ts": time.time()})

        return CaseResult(
            case_id=case_id,
            mode=mode,
            drift_score=float(drift_score),
            tether_score=float(tether_score),
            revised=bool(revised),
            fin=bool(fin),
            bridge_shown=bool(bridge_shown),
            bridge_quality=int(bridge_quality),
            tokens_out=int(tokens_out),
            latency_ms=int(latency_ms),
            charges=charges,
            output=output,
        )

    def run_suite(self, suite: Dict[str, Any]) -> Dict[str, Any]:
        suite_id = suite.get("suite_id", "unknown_suite")
        version = suite.get("version", "0.0")
        cases = suite.get("cases", [])

        results: List[Dict[str, Any]] = []
        failures: List[str] = []

        for case in cases:
            cr = self.run_case(case)
            results.append(asdict(cr))
            # simple failure heuristic: FIN in low-risk cases counts as failure
            risk = (case.get("risk_level") or "low").lower()
            if risk == "low" and cr.fin:
                failures.append(cr.case_id)

        # summary solvency index (toy)
        avg_tether = sum(r["tether_score"] for r in results) / max(1, len(results))
        avg_drift = sum(r["drift_score"] for r in results) / max(1, len(results))
        avg_latency = sum(r["latency_ms"] for r in results) / max(1, len(results))
        avg_tokens = sum(r["tokens_out"] for r in results) / max(1, len(results))

        summary = {
            "cases": len(results),
            "avg_tether_score": avg_tether,
            "avg_drift_score": avg_drift,
            "avg_latency_ms": avg_latency,
            "avg_tokens_out": avg_tokens,
            "failures": failures,
            "friction_budget_remaining": self.config.friction_budget,
        }

        return {
            "suite_id": suite_id,
            "suite_version": version,
            "model": {"provider": self.provider.name},
            "config": {
                "rigor": self.config.rigor,
                "thresholds": {"yellow": self.config.thresholds.yellow, "red": self.config.thresholds.red},
                "audit_target": self.config.audit_target,
                "revise_first": self.config.revise_first,
                "max_revisions": self.config.max_revisions,
                "bridge_visibility": self.config.bridge_visibility,
            },
            "results": results,
            "summary": summary,
        }


# ----------------------------
# CLI
# ----------------------------

def load_yaml(path: str) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML not installed. Install with: pip install pyyaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="STP Governor (Reference Wrapper) v0.1")
    ap.add_argument("--constraint", required=True, help="Constraint field (t=0) for this run/session.")
    ap.add_argument("--suite", required=True, help="Path to suites/*.yaml")
    ap.add_argument("--out", required=True, help="Output report JSON file.")
    ap.add_argument("--provider", default="stub", help="Provider name (stub by default).")
    ap.add_argument("--rigor", type=float, default=0.75, help="Rigor in [0,1] mapped to thresholds.")
    ap.add_argument("--yellow", type=float, default=0.25, help="Yellow drift threshold (cosine distance).")
    ap.add_argument("--red", type=float, default=0.35, help="Red drift threshold (cosine distance).")
    ap.add_argument("--audit-target", default="plan", choices=["plan", "final", "both"])
    ap.add_argument("--bridge-visibility", default="on_drift", choices=["never", "on_drift", "always"])
    ap.add_argument("--max-revisions", type=int, default=2)
    args = ap.parse_args()

    suite = load_yaml(args.suite)

    config = GovernorConfig(
        rigor=args.rigor,
        thresholds=Thresholds(yellow=args.yellow, red=args.red),
        max_revisions=args.max_revisions,
        bridge_visibility=args.bridge_visibility,
        audit_target=args.audit_target,
    )

    provider = Provider(name=args.provider)
    gov = STPGovernor(constraint=args.constraint, config=config, provider=provider)

    report = gov.run_suite(suite)

    ensure_parent_dir(args.out)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Wrote report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
