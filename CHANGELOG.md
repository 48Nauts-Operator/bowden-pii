# v0.0.1 — Developer preview

Initial public release of the Bowden-PII local redaction runtime.

- Python API and command-line tool for supported Swiss/EU identifiers.
- Checksum-aware validators, three policies, consistent typed placeholders,
  a local replacement map, and audit metadata without raw detected values.
- Experimental hybrid interfaces, focused tests, and a small synthetic smoke fixture.
- Python 3.11+; no dependencies or model required for the default rules engine.

Download the wheel or source archive below. See the README for installation.
This pre-release does not include trained models, training datasets, research
tools, or production-readiness guarantees. Neural model integration remains
experimental, and its current adapter does not chunk long inputs.
