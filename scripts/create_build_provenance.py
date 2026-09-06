from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--sbom", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    artifact = Path(args.artifact)
    sbom = Path(args.sbom)
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {"name": artifact.name, "digest": {"sha256": sha256(artifact)}},
            {"name": sbom.name, "digest": {"sha256": sha256(sbom)}},
        ],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://github.com/jadeldiaz01-png/Agentic-Al-Brief/build/python-wheel@v1",
                "externalParameters": {"source_sha": args.source_sha},
                "internalParameters": {"reproducibility_check": "two-build-sha256-match"},
                "resolvedDependencies": [
                    {
                        "uri": "git+https://github.com/jadeldiaz01-png/Agentic-Al-Brief",
                        "digest": {"sha1": args.source_sha},
                    }
                ],
            },
            "runDetails": {
                "builder": {"id": "https://github.com/actions/runner"},
                "metadata": {"invocationId": args.source_sha},
                "byproducts": [],
            },
        },
    }
    Path(args.output).write_text(json.dumps(statement, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
