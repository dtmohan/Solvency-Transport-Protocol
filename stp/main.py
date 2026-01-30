import sys
import yaml
import uuid
from stp.governor import STPKernel, SolvencyZone
from stp.auditor import InternalEarAuditor

# Mock Inference Engine for demonstration
class MockInference:
    def embed(self, text):
        import numpy as np
        # Simulate a 1536-dim vector based on text content
        val = sum(ord(c) for c in text) % 100 / 100.0
        vec = np.zeros(1536)
        vec[0] = val
        return vec / (np.linalg.norm(vec) + 1e-9)

def run_suite(suite_path: str, config_path: str, report_path: str):
    # Initialize Auditor and Governor
    auditor = InternalEarAuditor(vector_engine=MockInference())
    governor = STPKernel(config_path=config_path, auditor=auditor)

    # Load Validation Suite (YAML)
    with open(suite_path, 'r') as f:
        suite = yaml.safe_load(f)

    print(f"--- Starting STP Governance Session [{governor.nonce}] ---")

    for test_case in suite.get('test_vectors', []):
        tx_id = str(uuid.uuid4())[:8]
        prompt = test_case['input']
        
        # Simulate Host generating a candidate response
        candidate_response = f"Simulated response for: {prompt[:30]}..."
        
        # Process through the Governor
        zone, message = governor.process_turn(candidate_response, tx_id)
        
        print(f"[TX:{tx_id}] Zone: {zone.name} | Action: {message}")

        # If Yellow, simulate a Bridge Artifact (Paid Motion)
        if zone == SolvencyZone.YELLOW:
            bridge = {
                "origin_ref": {
                    "constraint_hash": governor.c_hash,
                    "session_nonce": governor.nonce
                },
                "constraint_clause": governor.c,
                "struts": [
                    {"step": 1, "premise": "A", "justification": "X"},
                    {"step": 2, "premise": "B", "justification": "Y"},
                    {"step": 3, "premise": "C", "justification": "Z"}
                ],
                "failure_condition": "Logic decouple detected."
            }
            if governor.verify_bridge(bridge):
                print(f"      ✅ Bridge Tax Paid. Session Solvent.")

    # Save final 2020-12 Schema compliant report
    governor.save_report(report_path)
    print(f"--- Session FIN. Report saved to: {report_path} ---")

if __name__ == "__main__":
    run_suite(
        suite_path="suites/stp_v2_validation.yaml",
        config_path="eval/deployment_config.json",
        report_path="eval/session_report.json"
    )
