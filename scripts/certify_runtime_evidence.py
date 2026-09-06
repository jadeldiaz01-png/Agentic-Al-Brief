from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentic_ai_brief.runtime_evidence import certify_runtime_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    raw = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit("RUNTIME_EVIDENCE_INVALID")
    cert = certify_runtime_bundle(raw, args.expected_sha)
    output = {
        "source_sha": cert.source_sha,
        "decision": cert.decision,
        "blockers": list(cert.blockers),
        "evidence_sha256": cert.evidence_sha256,
    }
    Path(args.output).write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))
    return 0 if cert.decision == "RUNTIME_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
