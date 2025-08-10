"""
Asynchronous file sorter.

Reads all files from the given source directory (recursively) and copies them
to the output directory, grouping them into subdirectories based on file
extension.

Rules:
- Hidden dirs/files (names starting with '.') are skipped.
- Known service dirs are excluded: .git, .idea, node_modules, __pycache__.
- No extension or "non-sensical" extensions (numeric/garbage) go to 'no_extension/'.
- Multi-suffix archives like '.tar.gz' are grouped as 'tar.gz/'.

Usage:
    python async_file_sorter.py --source /path/to/source --output /path/to/output
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import shutil
from pathlib import Path
from typing import Iterable, List, Optional, Set


# Explicitly excluded directories
EXCLUDED_DIRS: Set[str] = {".git", ".idea", "node_modules", "__pycache__"}


def setup_logging() -> None:
    """Configure logging with a concise format."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )


def _extension_folder_name(path: Path) -> str:
    """
    Determine destination subfolder name based on file extension.

    Rules:
    - Multi-suffix extensions (e.g., '.tar.gz') become 'tar.gz'.
    - Accept alphanumeric parts (letters and/or digits).
    - Reject purely numeric or garbage extensions (e.g., '.000000002') -> 'no_extension'.
    - Allow certain known numeric-first formats (e.g., '7z', '3gp', '3g2').

    Args:
        path: Path object for the file.

    Returns:
        A string with the normalized extension or 'no_extension'.
    """
    # Extract all suffix parts without leading dots, lowercased
    parts = [s.lstrip(".").lower() for s in path.suffixes]  # e.g. ['tar', 'gz'] for .tar.gz
    if not parts:
        return "no_extension"

    joined = ".".join(parts)

    # Allowed numeric-first formats
    allow_numeric_only = {"7z", "3gp", "3g2"}

    # All parts must be alphanumeric (letters and/or digits)
    if all(p.isalnum() for p in parts):
        # At least one part should contain a letter OR be in the allowlist
        if any(any(ch.isalpha() for ch in p) for p in parts) or joined in allow_numeric_only:
            return joined

    return "no_extension"


def _should_skip(path: Path) -> bool:
    """Return True if the path should be skipped based on hidden/excluded dirs."""
    # Skip hidden files/dirs anywhere in the path
    if any(part.startswith(".") for part in path.parts):
        return True
    # Skip explicitly excluded directories
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return True
    return False


async def _copy_file_async(src: Path, dst_dir: Path) -> None:
    """
    Copy a single file into 'dst_dir' asynchronously (offloaded to a thread).

    Uses shutil.copy2 to preserve metadata.
    """
    try:
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / src.name
        await asyncio.to_thread(shutil.copy2, src, dst)
        logging.debug("Copied: %s -> %s", src, dst)
    except Exception as exc:
        logging.error("Failed to copy %s: %s", src, exc)


async def copy_file(src_file: Path, out_root: Path) -> None:
    """
    Determine destination subfolder (by sanitized extension) and copy the file.
    Numeric/invalid extensions are treated as no_extension.
    """
    subfolder = _extension_folder_name(src_file)
    dst_dir = out_root / subfolder
    await _copy_file_async(src_file, dst_dir)


async def read_folder(
    source_root: Path,
    out_root: Path,
    *,
    include_exts: Optional[Iterable[str]] = None,
    max_concurrency: int = 64,
) -> None:
    """
    Recursively scan 'source_root', schedule async copies into 'out_root'
    grouping by (sanitized) extension.

    Args:
        source_root: Directory to scan recursively.
        out_root: Destination directory root.
        include_exts: Optional set of allowed basic extensions (e.g., {".txt", ".md"}).
                      Comparison is case-insensitive and looks only at the last suffix.
        max_concurrency: Limit for concurrent copy operations.
    """
    sem = asyncio.Semaphore(max_concurrency)
    tasks: List[asyncio.Task] = []

    norm_exts: Optional[Set[str]] = None
    if include_exts:
        norm_exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in include_exts}

    for path in source_root.rglob("*"):
        if not path.is_file():
            continue
        if _should_skip(path):
            continue
        if norm_exts and path.suffix.lower() not in norm_exts:
            continue

        async def _task(p: Path) -> None:
            async with sem:
                await copy_file(p, out_root)

        tasks.append(asyncio.create_task(_task(path)))

    if not tasks:
        logging.info("No files found to process.")
        return

    logging.info("Scheduled %d file(s) for copy.", len(tasks))
    await asyncio.gather(*tasks)


def parse_args() -> argparse.Namespace:
    """Parse required CLI arguments."""
    parser = argparse.ArgumentParser(description="Asynchronously sort files by extension.")
    parser.add_argument("--source", required=True, help="Path to the source directory (recursive).")
    parser.add_argument("--output", required=True, help="Path to the output directory.")
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
    setup_logging()
    args = parse_args()

    src = Path(args.source).resolve()
    dst = Path(args.output).resolve()

    if not src.is_dir():
        raise SystemExit(f"[ERROR] Source directory is not a directory or does not exist: {src}")

    dst.mkdir(parents=True, exist_ok=True)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start = loop.time()
    try:
        loop.run_until_complete(read_folder(src, dst, include_exts=None, max_concurrency=64))
    finally:
        elapsed = loop.time() - start
        logging.info("Completed in %.3f s", elapsed)
        loop.close()


if __name__ == "__main__":
    main()
