"""Run the experimental candidate discovery prototype on one real SSS image."""

import json
from pathlib import Path

from app.config import OUTPUTS_DIR
from app.services.candidate_discovery import ExperimentalCandidateDiscovery


IMAGE_PATH = Path(__file__).resolve().parent / "test_dataimages" / "images" / "Viator_071.png"
OUTPUT_DIR = OUTPUTS_DIR / "experimental_candidate_discovery_viator_07"


def main() -> None:
    result = ExperimentalCandidateDiscovery().discover(IMAGE_PATH, OUTPUT_DIR)
    report_path = OUTPUT_DIR / "candidate_report.json"
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"report: {report_path}")


if __name__ == "__main__":
    main()
