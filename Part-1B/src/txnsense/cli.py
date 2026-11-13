"""`txnsense parse "<sms>" [--received-at ISO] [--sender ID]` (FR-008)."""

from __future__ import annotations

import argparse
import json
import sys

from txnsense.llm import ModelServiceError
from txnsense.parser import parse_sms


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="txnsense", description="Parse a bank/UPI SMS.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse")
    p.add_argument("text")
    p.add_argument("--received-at")
    p.add_argument("--sender")
    args = ap.parse_args(argv)
    try:
        result = parse_sms(args.text, args.received_at, args.sender)
    except ModelServiceError as exc:
        print(f"error: model service unavailable ({exc})", file=sys.stderr)
        return 3
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
