# SPDX-License-Identifier: Apache-2.0
"""Build the separate Catalogue 2 candidate; never publish or activate it."""
import argparse
from pathlib import Path
from catalogue_evidence_driver import build_candidate
from publication_contract import parse_catalogue, digest

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/catalogue')
    args = parser.parse_args()
    try:
        raw = build_candidate(ROOT)
        document = parse_catalogue(raw)
        args.output.mkdir(parents=True, exist_ok=True)
        for name in ('catalogue.json', f"catalogue-{document['sequence']:06d}.json"):
            with (args.output / name).open('xb') as stream:
                stream.write(raw)
    except (ValueError, OSError):
        parser.exit(1, 'catalogue_candidate_build_rejected\n')
    print(f"candidate sequence={document['sequence']} sha256:{digest(raw)}; not publication authority")


if __name__ == '__main__':
    main()
