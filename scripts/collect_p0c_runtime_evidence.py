from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentic_ai_brief.p0c_evidence import build_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--execution-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    bundle = build_bundle(Path(args.evidence_dir), args.expected_sha, args.execution_id)
    Path(args.output).write_text(json.dumps(bundle, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
