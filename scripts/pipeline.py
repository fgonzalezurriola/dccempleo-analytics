from __future__ import annotations

import argparse
import asyncio
import os

from _bootstrap import ensure_project_root_on_path

ensure_project_root_on_path()

from analyze_data import run_analysis
from build_dist import build_dist
from label_with_llm import run_labeling
from scrape_telegram import run_export


def run_pipeline(
    *,
    skip_scrape: bool,
    skip_labeling: bool,
    skip_dist: bool,
) -> None:
    if not skip_scrape:
        asyncio.run(run_export())
    else:
        print("skip scrape enabled")

    if not skip_labeling:
        batch_size = int(os.environ.get("LABEL_BATCH_SIZE", "5"))
        delay_seconds = float(os.environ.get("LABEL_DELAY_SECONDS", "0.8"))
        stop_after_error_batches = int(os.environ.get("LABEL_STOP_AFTER_ERROR_BATCHES", "3"))
        retries = int(os.environ.get("LABEL_RETRIES", "2"))
        retry_delay_seconds = float(os.environ.get("LABEL_RETRY_DELAY_SECONDS", "0.7"))
        try:
            asyncio.run(
                run_labeling(
                    batch_size=batch_size,
                    delay_seconds=delay_seconds,
                    stop_after_error_batches=stop_after_error_batches,
                    retries=retries,
                    retry_delay_seconds=retry_delay_seconds,
                )
            )
        except RuntimeError as exc:
            raise SystemExit(f"ERROR: {exc}") from exc
    else:
        print("skip labeling enabled")

    run_analysis()

    if not skip_dist:
        build_dist()
    else:
        print("skip dist enabled")


def main() -> None:
    parser = argparse.ArgumentParser(description="Full pipeline for dccempleo-analytics.")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip Telegram scraping.")
    parser.add_argument("--skip-labeling", action="store_true", help="Skip LLM labeling.")
    parser.add_argument("--skip-dist", action="store_true", help="Skip static dist generation.")
    args = parser.parse_args()

    run_pipeline(
        skip_scrape=args.skip_scrape,
        skip_labeling=args.skip_labeling,
        skip_dist=args.skip_dist,
    )


if __name__ == "__main__":
    main()
