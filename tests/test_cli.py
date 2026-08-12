"""Focused tests for rmd command behavior."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rmd.cli import cleaned_path, main, remove_metadata


class CleanedPathTests(unittest.TestCase):
    """Verify that output paths cannot overwrite existing files."""

    def test_adds_cleaned_suffix_before_extension(self):
        """A normal filename receives a readable cleaned suffix."""
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(cleaned_path(Path(directory) / "photo.jpg").name, "photo.cleaned.jpg")

    def test_increments_when_default_output_exists(self):
        """An existing cleaned copy causes rmd to choose a new name."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "photo.jpg"
            source.touch()
            (Path(directory) / "photo.cleaned.jpg").touch()
            self.assertEqual(cleaned_path(source).name, "photo.cleaned-2.jpg")


class RemovalTests(unittest.TestCase):
    """Verify the safety boundary around the ExifTool invocation."""

    def test_copies_original_before_invoking_exiftool(self):
        """Cleaning writes to a copy and requests removal of all writable tags."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "photo.jpg"
            destination = Path(directory) / "photo.cleaned.jpg"
            source.write_bytes(b"original")
            completed = subprocess.CompletedProcess([], 0)
            with patch("rmd.cli.subprocess.run", return_value=completed) as run:
                self.assertIsNone(remove_metadata(source, destination, "exiftool"))
            self.assertEqual(destination.read_bytes(), b"original")
            run.assert_called_once_with(
                ["exiftool", "-all=", "-overwrite_original", str(destination)],
                check=False,
                capture_output=True,
                text=True,
            )


class MainTests(unittest.TestCase):
    """Verify user-visible validation and dry-run behavior."""

    def test_dry_run_needs_no_exiftool_and_creates_no_copy(self):
        """Dry runs report the planned target without modifying the filesystem."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "photo.jpg"
            source.touch()
            with patch("rmd.cli.shutil.which", return_value=None):
                self.assertEqual(main(["--dry-run", str(source)]), 0)
            self.assertFalse((Path(directory) / "photo.cleaned.jpg").exists())

    def test_directory_requires_recursive_option(self):
        """Directories are rejected unless callers explicitly opt into traversal."""
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(main([directory]), 2)

    def test_missing_exiftool_is_a_clear_error(self):
        """Normal runs explain the sole runtime dependency before copying files."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "photo.jpg"
            source.touch()
            with patch("rmd.cli.shutil.which", return_value=None):
                self.assertEqual(main([str(source)]), 2)


if __name__ == "__main__":
    unittest.main()
