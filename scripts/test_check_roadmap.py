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
        (self.root / "docs/history").mkdir(parents=True)
        self.write("docs/roadmap/M1-NOTES.md", "Synthetic current handoff.\n")
        for name in ("AGENTS.md", "README.md", "docs/roadmap/EXECUTION.md"):
            self.write(name, "Synthetic documentation fixture.\n")
        self.write("docs/roadmap/EVIDENCE.md", "| Criterion | Kind | Artifact | Result |\n|---|---|---|---|\n")
        self.write("material.md", "Synthetic document evidence for parser tests.\n")
        self.write("owner-review.md", "Synthetic fixture; not a real owner's approval.\n")
        self.write("docs/history/REVISIONS.md", "| Retired ID | Evidence kinds | Original requirement | Replaced by |\n|---|---|---|---|\n")
        archived = "# Historical synthetic scenarios\n"
        for scenario in range(1, 26):
            archived += f"### S{scenario} — Archived scenario\n\n"
        archived += "| ID | Trigger | Decision | State |\n|---|---|---|---|\n"
        for scenario in range(1, 26):
            archived += f"| S{scenario} | Event | Wait | Saved |\n"
        self.write("docs/history/M1-2026-09-17.md", archived)
        roadmap = "| Milestone | File | Goal | Status |\n|---|---|---|---|\n"
        for number in range(1, 6):
            status = "in progress" if number == 1 else "pending"
            roadmap += f"| M{number} | M{number}.md | Fixture | {status} |\n"
            content = f"# M{number}\n\n> Status: {status}\n\n"
            if number == 1:
                for scenario in range(26, 36):
                    content += f"### S{scenario} — Scenario title\n\n"
                content += "| ID | Trigger | Decision | State |\n|---|---|---|---|\n"
                for scenario in range(26, 36):
                    content += f"| S{scenario} | Event | Wait | Saved |\n"
                for criterion in range(1, 5):
                    kinds = "owner" if criterion == 1 else "document, owner"
                    content += f"- [ ] **M1-E{criterion}** ({kinds}) Owner reviews material.\n"
            else:
                content += f"- [ ] **M{number}-E1** (document) Fixture criterion.\n"
            self.write(f"docs/roadmap/M{number}.md", content)
        for number in range(1, 8):
            roadmap += f"- **CP{number} — Synthetic contract.** Fixture wording.\n"
        self.write("Roadmap.md", roadmap)
        m1 = (self.root / "docs/roadmap/M1.md").read_text()
        m1 += "| Contract | Scenarios | Current criteria |\n|---|---|---|\n"
        for number in range(1, 8):
            m1 += f"| CP{number} | S26 | M2-E1 |\n"
        self.write("docs/roadmap/M1.md", m1)

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
        self.replace("docs/roadmap/M1.md", "| S35 |", "| S34 |")
        self.assertIn("Current M1 walkthrough must contain S26–S35 exactly once", validate(self.root))

    def test_heading_id_must_match_exactly(self) -> None:
        self.replace("docs/roadmap/M1.md", "### S26 —", "### S26extra —")
        self.assertIn("Current M1 scenario headings must contain S26–S35 exactly once", validate(self.root))

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

    def test_presence_scenario_cannot_disappear(self) -> None:
        self.replace("docs/roadmap/M1.md", "### S26 — Scenario title", "### Unnumbered scenario")
        self.assertIn("Current M1 scenario headings must contain S26–S35 exactly once", validate(self.root))

    def test_presence_definition_and_traceability_are_required(self) -> None:
        self.replace("Roadmap.md", "**CP2 —", "**Presence —")
        self.assertIn("Roadmap must define CP1–CP7 exactly once", validate(self.root))
        self.replace("docs/roadmap/M1.md", "| CP3 | S26 | M2-E1 |", "| CP3 | S999 | M2-E999 |")
        errors = validate(self.root)
        self.assertIn("M1 CP3: unknown or missing scenario mapping", errors)
        self.assertIn("M1 CP3: mappings must reference current acceptance criteria", errors)

    def retire_fixture(self) -> None:
        """Preserve one old criterion while introducing a distinct replacement."""
        self.replace("docs/roadmap/M2.md", "M2-E1", "M2-E7")
        self.replace("docs/roadmap/M1.md", "| M2-E1 |", "| M2-E7 |")
        path = self.root / "docs/history/REVISIONS.md"
        with path.open("a") as handle:
            handle.write("| M2-E1 | document | Old fixture requirement. | M2-E7 |\n")

    def test_retired_evidence_does_not_approve_replacement(self) -> None:
        self.retire_fixture()
        self.evidence("M2-E1", "document")
        self.assertEqual(validate(self.root), [])
        self.replace("docs/roadmap/M2.md", "- [ ] **M2-E7**", "- [x] **M2-E7**")
        self.assertIn("M2-E7: checked without passing evidence for document", validate(self.root))

    def test_retired_id_cannot_be_reused_or_back_presence(self) -> None:
        self.retire_fixture()
        self.replace("docs/roadmap/M1.md", "| CP1 | S26 | M2-E7 |", "| CP1 | S26 | M2-E1 |")
        self.assertIn("M1 CP1: mappings must reference current acceptance criteria", validate(self.root))
        self.replace("docs/roadmap/M2.md", "M2-E7", "M2-E1")
        self.assertIn("REVISIONS M2-E1: retired ID is duplicated or reused as an active criterion", validate(self.root))

    def test_retirement_must_reference_a_current_replacement(self) -> None:
        self.retire_fixture()
        self.replace("docs/history/REVISIONS.md", "| M2-E7 |", "| M2-E999 |")
        self.assertIn("REVISIONS M2-E1: replacement IDs must name current criteria", validate(self.root))

    def test_archived_scenarios_cannot_disappear(self) -> None:
        self.replace("docs/history/M1-2026-09-17.md", "| S25 |", "| S24 |")
        self.assertIn("Archived M1 walkthrough must contain S1–S25 exactly once", validate(self.root))

    def test_archived_scenario_cannot_replace_current_scenario(self) -> None:
        self.replace("docs/roadmap/M1.md", "### S26 — Scenario title", "### S1 — Archived substitute")
        self.replace("docs/roadmap/M1.md", "| CP1 | S26 |", "| CP1 | S1 |")
        errors = validate(self.root)
        self.assertIn("Current M1 scenario headings must contain S26–S35 exactly once", errors)
        self.assertIn("M1 CP1: unknown or missing scenario mapping", errors)

    def test_only_completed_handoffs_can_be_archived(self) -> None:
        current = self.root / "docs/roadmap/M1-NOTES.md"
        archived = self.root / "docs/history/M1-NOTES.md"
        current.rename(archived)
        self.assertIn("M1: active milestone needs docs/roadmap/M1-NOTES.md", validate(self.root))
        self.replace("docs/roadmap/M1.md", "Status: in progress", "Status: complete")
        self.replace("Roadmap.md", "| M1 | M1.md | Fixture | in progress |", "| M1 | M1.md | Fixture | complete |")
        for number in range(1, 5):
            criterion = f"M1-E{number}"
            self.check_criterion(criterion)
            self.evidence(criterion, "owner")
            if number > 1:
                self.evidence(criterion, "document")
        self.assertEqual(validate(self.root), [])
        archived.unlink()
        self.assertIn("M1: complete milestone needs a current or archived M1-NOTES.md", validate(self.root))


if __name__ == "__main__":
    unittest.main()
