"""Tests for final project artifact and documentation checks."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from check_project import _verify_markdown_links


class ProjectHealthCheckTests(unittest.TestCase):
    """Validate the local Markdown-link integrity helper."""

    def test_accepts_valid_local_and_external_targets(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            assets = root / "assets"
            assets.mkdir()
            (assets / "note.md").write_text("# Note\n", encoding="utf-8")
            (assets / "figure.png").write_bytes(b"figure")

            document = root / "README.md"
            document.write_text(
                "\n".join(
                    [
                        "[Local note](assets/note.md#details)",
                        "![Figure](assets/figure.png)",
                        "[Section](#results)",
                        "[Website](https://example.com)",
                    ]
                ),
                encoding="utf-8",
            )

            with redirect_stdout(StringIO()):
                _verify_markdown_links([document])

    def test_reports_missing_target(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            document = Path(temporary_directory) / "README.md"
            document.write_text(
                "[Missing](assets/missing.md#section)\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(FileNotFoundError, "assets/missing.md"):
                _verify_markdown_links([document])


if __name__ == "__main__":
    unittest.main()
