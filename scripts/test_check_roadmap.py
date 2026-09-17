"""Regression checks for formatting tolerance and acceptance bookkeeping."""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from check_roadmap import validate


class RoadmapChecks(unittest.TestCase):
    """Use synthetic documents so tests never alter real acceptance records."""

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix="enthus-roadmap-test-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "docs/roadmap").mkdir(parents=True)
        for name in ("AGENTS.md", "README.md", "docs/roadmap/EXECUTION.md"):
            self.write(name, "Synthetic documentation fixture.\n")
        self.write("docs/roadmap/EVIDENCE.md", "| Criterion | Kind | Artifact | Result |\n|---|---|---|---|\n")
        self.write("material.md", "Synthetic document evidence for parser tests.\n")
        self.write("owner-review.md", "Synthetic fixture; not a real owner's approval.\n")
        roadmap = "| Milestone | File | Goal | Status |\n|---|---|---|---|\n"
        for number in range(1, 6):
            status = "in progress" if number == 1 else "pending"
            roadmap += f"| M{number} | M{number}.md | Fixture | {status} |\n"
            content = f"# M{number}\n\n> Status: {status}\n\n"
            if number == 1:
                for scenario in range(1, 26):
                    content += f"### S{scenario} — Scenario title\n\n"
                content += "| ID | Trigger | Decision | State |\n|---|---|---|---|\n"
                for scenario in range(1, 26):
                    content += f"| S{scenario} | Event | Wait | Saved |\n"
                for criterion in range(1, 5):
                    kinds = "owner" if criterion == 1 else "document, owner"
                    content += f"- [ ] **M1-E{criterion}** ({kinds}) Owner reviews material.\n"
            else:
                content += f"- [ ] **M{number}-E1** (document) Fixture criterion.\n"
            self.write(f"docs/roadmap/M{number}.md", content)
        self.write("Roadmap.md", roadmap)

    def write(self, name: str, content: str) -> None:
        (self.root / name).write_text(content, encoding="utf-8")

    def replace(self, name: str, old: str, new: str) -> None:
        content = (self.root / name).read_text(encoding="utf-8")
        self.assertIn(old, content)
        self.write(name, content.replace(old, new))

    def evidence(self, criterion: str, kind: str, result: str = "pass") -> None:
        artifact = "owner-review.md" if kind == "owner" else "material.md"
        path = self.root / "docs/roadmap/EVIDENCE.md"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"| {criterion} | {kind} | `{artifact}` | {result} |\n")

    def check_criterion(self, criterion: str) -> None:
        self.replace("docs/roadmap/M1.md", f"- [ ] **{criterion}**", f"- [x] **{criterion}**")

    def test_baseline(self) -> None:
        self.assertEqual(validate(self.root), [])

    def test_common_heading_separators(self) -> None:
        original = (self.root / "docs/roadmap/M1.md").read_text()
        for dash in ("-", "–", "—"):
            with self.subTest(dash=dash):
                varied = re.sub(r"^### S(\d+) — ", rf"  ###   S\1  {dash}   ", original, flags=re.M)
                self.write("docs/roadmap/M1.md", varied)
                self.assertEqual(validate(self.root), [])

    def test_table_padding_and_optional_trailing_pipe(self) -> None:
        self.check_criterion("M1-E2")
        self.evidence("M1-E2", "document")
        self.evidence("M1-E2", "owner")
        # Cover roadmap, walkthrough, and evidence parsing with the same reformat.
        for name in ("Roadmap.md", "docs/roadmap/M1.md", "docs/roadmap/EVIDENCE.md"):
            lines = (self.root / name).read_text().splitlines()
            for index, line in enumerate(lines):
                if line.startswith("|"):
                    cells = [cell.strip() for cell in line.strip("|").split("|")]
                    lines[index] = "  |" + "|".join(cells)
            self.write(name, "\n".join(lines) + "\n")
        self.assertEqual(validate(self.root), [])

    def test_acceptance_and_status_padding(self) -> None:
        self.replace("docs/roadmap/M1.md", "- [ ] **", "  -   [ ]   **")
        self.replace("docs/roadmap/M1.md", "> Status: in progress", "  >  Status:   in progress   ")
        self.assertEqual(validate(self.root), [])

    def test_duplicate_and_missing_walkthrough_ids(self) -> None:
        self.replace("docs/roadmap/M1.md", "| S25 |", "| S24 |")
        self.assertIn("M1 walkthrough must contain S1–S25 exactly once", validate(self.root))

    def test_heading_id_must_match_exactly(self) -> None:
        self.replace("docs/roadmap/M1.md", "### S11 —", "### S11extra —")
        self.assertIn("M1 scenario headings must contain S1–S25 exactly once", validate(self.root))

    def test_review_material_alone_cannot_approve_e2_through_e4(self) -> None:
        for number in (2, 3, 4):
            criterion = f"M1-E{number}"
            self.check_criterion(criterion)
            self.evidence(criterion, "document")
            self.assertIn(f"{criterion}: checked without passing evidence for owner", validate(self.root))

    def test_owner_evidence_does_not_replace_review_material(self) -> None:
        self.check_criterion("M1-E2")
        self.evidence("M1-E2", "owner")
        self.assertIn("M1-E2: checked without passing evidence for document", validate(self.root))

    def test_scoped_owner_review_can_support_multiple_criteria(self) -> None:
        for number in (2, 3, 4):
            criterion = f"M1-E{number}"
            self.check_criterion(criterion)
            self.evidence(criterion, "document")
            self.evidence(criterion, "owner")
        self.assertEqual(validate(self.root), [])

    def test_new_failure_invalidates_older_pass(self) -> None:
        self.check_criterion("M1-E2")
        self.evidence("M1-E2", "document")
        self.evidence("M1-E2", "owner")
        self.evidence("M1-E2", "owner", "fail")
        self.assertIn("M1-E2: checked without passing evidence for owner", validate(self.root))

    def test_format_tolerance_does_not_allow_skipping_milestones(self) -> None:
        self.replace("docs/roadmap/M2.md", "Status: pending", "Status: in progress")
        self.replace("Roadmap.md", "| M2 | M2.md | Fixture | pending |", "|M2|M2.md|Fixture|in progress|")
        self.assertIn("M2: cannot advance before predecessor milestones complete", validate(self.root))


if __name__ == "__main__":
    unittest.main()
