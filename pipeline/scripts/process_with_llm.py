from __future__ import annotations

import argparse
import asyncio

from _bootstrap import ensure_project_root_on_path

ensure_project_root_on_path()

from analyze_data import run_analysis
from label_with_llm import run_labeling


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run LLM labeling and analysis."
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Deprecated. Build is now a separate command: scripts/build_web.py.",
    )
    args = parser.parse_args()

    try:
        asyncio.run(run_labeling())
    except RuntimeError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc

    run_analysis()
    if args.skip_build:
        print("skip build enabled (deprecated; build is separate now).")


if __name__ == "__main__":
    main()
