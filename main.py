import yaml
import uuid
import numpy as np
import os
from stp.governor import STPKernel, SolvencyZone
from stp.auditor import InternalEarAuditor

class MockInference:
    """
    Mock tailored for Panther Lake Silicon Validation.
    It simulates semantic drift based on hardware power/thermal states.
    """
    def embed(self, text):
        text_lower = text.lower()
        vec = np.zeros(1536)
        vec[0] = 1.0  # The Invariant Axis (Strict Panther Lake Specs)
        
        # Test Case 1: Sub-zero efficiency (Yellow Drift)
        if "efficiency" in text_lower or "sub-zero" in text_lower:
            # Targeted Drift ≈ 0.0829 (YELLOW Zone for T1=0.05)
            vec[0] = 0.92
            vec[1] = 0.40
            print(f"DEBUG: Internal Ear detected Hardware Friction...")
            
        # Test Case 2: Silicon Validation Bypass (Red Drift)
        elif "ignore" in text_lower or "validation constraint" in text_lower:
            # Targeted Drift ≈ 0.459 (RED Zone for T2=0.15)
            vec[0] = 0.50
            vec[1] = 0.85
            print(f"DEBUG: Internal Ear detected Insolvency...")

        return vec / (np.linalg.norm(vec) + 1e-9)

def run_suite(suite_path: str, config_path: str, report_path: str):
    # Initialize Core Modules
    auditor = InternalEarAuditor(vector_engine=MockInference())
    governor = STPKernel(config_path=config_path, auditor=auditor)

    if not os.path.exists(suite_path):
        print(f"Error: Suite file not found at {suite_path}")
        return

    with open(suite_path, 'r') as f:
        suite = yaml.safe_load(f)

    print(f"--- Starting STP Governance Session [{governor.nonce}] ---")

    for test_case in suite.get('test_vectors', []):
        tx_id = str(uuid.uuid4())[:8]
        prompt = test_case['input']
        candidate_response = f"Simulated output for: {prompt}"
        
        # Process through the Policy Engine
        zone, action = governor.process_turn(candidate_response, tx_id)
        
        print(f"[TX:{tx_id}] Zone: {zone.name} | Action: {action}")
        print(f"   Payload: {candidate_response}")

        # Hardware-specific Bridge Tax reconciliation
        if zone == SolvencyZone.YELLOW:
            print("   >> TRIGGERING BRIDGE TAX RECONCILIATION...")
            bridge = {
                "origin_ref": {"session_nonce": governor.nonce},
                "struts": [
                    {"step": 1, "premise": "Identify Hardware Constraint (PL1/PL2)"},
                    {"step": 2, "premise": "Reconcile Efficiency Claim via WPA Logs"},
                    {"step": 3, "premise": "Acknowledge Primary Invariant (Strict Validation)"}
                ],
                "status": "RECONCILED"
            }
            governor.verify_bridge(bridge)
            print("   >> BRIDGE RECONCILED. Continuing session.")

        print("-" * 40)

    governor.save_report(report_path)
    print(f"--- Session FIN. Report saved to: {report_path} ---")

if __name__ == "__main__":
    os.makedirs("eval", exist_ok=True)
    run_suite(
        suite_path="suites/panther_lake_v1.yaml",
        config_path="eval/deployment_config.json",
        report_path="eval/session_report.json"
    )
