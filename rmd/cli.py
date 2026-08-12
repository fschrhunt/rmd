"""Command-line interface for making metadata-free file copies."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Result:
    """The result of preparing one input file."""

    source: Path
    destination: Path
    error: str | None = None


def cleaned_path(source: Path) -> Path:
    """Return a non-conflicting default name for a cleaned copy of source."""
    suffix = "".join(source.suffixes)
    stem = source.name[: -len(suffix)] if suffix else source.name
    candidate = source.with_name(f"{stem}.cleaned{suffix}")
    number = 2
    while candidate.exists():
        candidate = source.with_name(f"{stem}.cleaned-{number}{suffix}")
        number += 1
    return candidate


def input_files(paths: Iterable[Path], recursive: bool) -> Iterable[Path]:
    """Yield regular input files, expanding directories only when requested."""
    for path in paths:
        if path.is_file():
            yield path
        elif path.is_dir() and recursive:
            yield from (child for child in path.rglob("*") if child.is_file())


def temporary_path(source: Path) -> Path:
    """Reserve a unique, same-directory temporary path that retains the file extension."""
    suffix = "".join(source.suffixes)
    stem = source.name[: -len(suffix)] if suffix else source.name
    descriptor, name = tempfile.mkstemp(prefix=f".{stem}.rmd-", suffix=suffix, dir=source.parent)
    os.close(descriptor)
    return Path(name)


def remove_metadata(source: Path, destination: Path, exiftool: str) -> str | None:
    """Copy source then ask ExifTool to remove every writable metadata tag."""
    shutil.copyfile(source, destination)
    completed = subprocess.run(
        [exiftool, "-all=", "-overwrite_original", str(destination)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        return None

    destination.unlink(missing_ok=True)
    detail = completed.stderr.strip() or completed.stdout.strip() or "ExifTool failed"
    return detail


def parser() -> argparse.ArgumentParser:
    """Create the command-line parser for rmd."""
    argument_parser = argparse.ArgumentParser(
        description="Remove embedded metadata using ExifTool without changing originals."
    )
    argument_parser.add_argument("paths", nargs="+", type=Path, help="Files to clean; drag them into the terminal.")
    argument_parser.add_argument("-r", "--recursive", action="store_true", help="Clean files inside supplied directories.")
    argument_parser.add_argument("--in-place", action="store_true", help="Replace each original after a successful cleanup.")
    argument_parser.add_argument("--dry-run", action="store_true", help="Show the files rmd would process.")
    argument_parser.add_argument("--exiftool", default="exiftool", help="ExifTool executable to use (default: exiftool).")
    return argument_parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run rmd and return a shell-compatible exit status."""
    args = parser().parse_args(argv)
    missing = [path for path in args.paths if not path.exists()]
    directories = [path for path in args.paths if path.is_dir()]
    if missing:
        for path in missing:
            print(f"rmd: not found: {path}", file=sys.stderr)
        return 2
    if directories and not args.recursive:
        print("rmd: directories require --recursive", file=sys.stderr)
        return 2

    files = []
    seen = set()
    for file in input_files(args.paths, args.recursive):
        resolved = file.resolve()
        if resolved not in seen:
            files.append(file)
            seen.add(resolved)
    if not files:
        print("rmd: no files found", file=sys.stderr)
        return 2

    if not args.dry_run and shutil.which(args.exiftool) is None:
        print("rmd: ExifTool is required. Install it, then try again.", file=sys.stderr)
        return 2

    results: list[Result] = []
    for source in files:
        destination = source if args.in_place else cleaned_path(source)
        if args.dry_run:
            print(f"Would clean: {source} -> {destination}")
            continue

        temporary = temporary_path(source) if args.in_place else destination
        error = remove_metadata(source, temporary, args.exiftool)
        if error is None and args.in_place:
            temporary.replace(source)
        results.append(Result(source, destination, error))

    for result in results:
        if result.error:
            print(f"Failed: {result.source}\n  {result.error}", file=sys.stderr)
        else:
            print(f"Cleaned: {result.source} -> {result.destination}")
    return 1 if any(result.error for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
