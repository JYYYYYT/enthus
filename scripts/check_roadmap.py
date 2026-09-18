#!/usr/bin/env python3
"""Check roadmap structure and evidence references, never evidence truth."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from collections.abc import Iterator
from pathlib import Path


KINDS = {"document", "replay", "live", "owner", "integration", "release"}
STATUSES = {"pending", "in progress", "complete"}
CRITERION = re.compile(
    r"^[ \t]{0,3}-[ \t]+\[([ xX])\][ \t]+\*\*(M[1-5]-E[1-9]\d*)\*\*"
    r"[ \t]+\(([^)\r\n]+)\)(?:[ \t]+|$)", re.M
)


def table_rows(content: str) -> Iterator[list[str]]:
    """Read pipe-delimited rows without treating padding as part of an ID."""
    for line in content.splitlines():
        row = line.strip()
        if not row.startswith("|"):
            continue
        row = row[1:]
        if row.endswith("|"):
            row = row[:-1]
        yield [cell.strip() for cell in row.split("|")]


def validate(root: Path) -> list[str]:
    """Return actionable failures without modifying the checkout."""
    root = root.resolve()
    errors: list[str] = []
    documents: dict[str, str] = {}
    names = ["AGENTS.md", "README.md", "Roadmap.md"] + [
        f"docs/roadmap/{name}.md"
        for name in ["EXECUTION", "EVIDENCE", "M1", "M2", "M3", "M4", "M5"]
    ] + ["docs/history/REVISIONS.md", "docs/history/M1-2026-09-17.md"]
    for name in names:
        path = root / name
        if not path.is_file():
            errors.append(f"Missing required document: {name}")
        else:
            documents[name] = path.read_text(encoding="utf-8")
    if errors:
        return errors

    # These are repository documentation links, not arbitrary Markdown or URLs.
    for name, content in documents.items():
        if len(re.findall(r"^```", content, re.M)) % 2:
            errors.append(f"{name}: unclosed code fence")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
            if "://" in target or target.startswith("#"):
                continue
            linked = (root / name).parent / target.split("#", 1)[0]
            if not linked.exists():
                errors.append(f"{name}: missing local link {target}")

    # Archiving an old contract must not erase it or mix it into the current proof.
    m1 = documents["docs/roadmap/M1.md"]
    for label, name, first, last in (
        ("Current M1", "docs/roadmap/M1.md", 26, 35),
        ("Archived M1", "docs/history/M1-2026-09-17.md", 1, 25),
    ):
        content = documents[name]
        expected = Counter(range(first, last + 1))
        # Common dash and spacing changes are editorial; IDs still match exactly.
        headings = Counter(int(value) for value in re.findall(
            r"^[ \t]{0,3}###[ \t]+S([1-9]\d*)[ \t]+[-–—][ \t]+\S[^\r\n]*$",
            content, re.M,
        ))
        walkthrough = Counter(
            int(row[0][1:]) for row in table_rows(content)
            if re.fullmatch(r"S[1-9]\d*", row[0])
        )
        if headings != expected:
            errors.append(f"{label} scenario headings must contain S{first}–S{last} exactly once")
        if walkthrough != expected:
            errors.append(f"{label} walkthrough must contain S{first}–S{last} exactly once")

    # Check traceability, not whether a paragraph or a runtime fulfills its meaning.
    presence_ids = Counter(f"CP{number}" for number in range(1, 8))
    definitions = Counter(re.findall(
        r"\*\*(CP[1-9]\d*)[ \t]+[-–—][ \t]+", documents["Roadmap.md"],
    ))
    if definitions != presence_ids:
        errors.append("Roadmap must define CP1–CP7 exactly once")
    presence_rows = [row for row in table_rows(m1) if re.fullmatch(r"CP[1-9]\d*", row[0])]
    if Counter(row[0] for row in presence_rows) != presence_ids:
        errors.append("M1 must map CP1–CP7 exactly once to scenarios and current criteria")

    statuses: list[str] = []
    criteria: dict[str, tuple[bool, set[str]]] = {}
    for number in range(1, 6):
        name = f"M{number}"
        content = documents[f"docs/roadmap/{name}.md"]
        status_matches = re.findall(r"^[ \t]{0,3}>[ \t]*Status:[ \t]*([^\r\n]+)$", content, re.M)
        status = status_matches[0].strip() if len(status_matches) == 1 else "invalid"
        statuses.append(status)
        if status not in STATUSES:
            errors.append(f"{name}: expected exactly one valid Status line")
        rows = [
            row for row in table_rows(documents["Roadmap.md"])
            if row[0] == name
        ]
        if len(rows) != 1 or len(rows[0]) != 4 or rows[0][-1] != status:
            errors.append(f"{name}: Roadmap table and milestone status disagree")

        matches = list(CRITERION.finditer(content))
        checkbox_count = len(re.findall(r"^[ \t]{0,3}-[ \t]+\[[ xX]\]", content, re.M))
        if not matches or len(matches) != checkbox_count:
            errors.append(f"{name}: every acceptance checkbox needs an ID and evidence kinds")
        for match in matches:
            marker, key, kinds_text = match.groups()
            kinds = {kind.strip() for kind in kinds_text.split(",")}
            if not key.startswith(f"{name}-E") or key in criteria:
                errors.append(f"{name}: misplaced or duplicate acceptance ID {key}")
            if not kinds or not kinds <= KINDS:
                errors.append(f"{key}: unknown evidence kinds {kinds_text}")
            criteria[key] = (marker.lower() == "x", kinds)

        if status == "complete":
            if any(match.group(1).lower() != "x" for match in matches):
                errors.append(f"{name}: complete milestone still has unchecked criteria")
            if not any((root / f"docs/{folder}/{name}-NOTES.md").is_file()
                       for folder in ("roadmap", "history")):
                errors.append(f"{name}: complete milestone needs a current or archived {name}-NOTES.md")
        if status == "in progress" and not (root / f"docs/roadmap/{name}-NOTES.md").is_file():
            errors.append(f"{name}: active milestone needs docs/roadmap/{name}-NOTES.md")
        if status in {"in progress", "complete"} and any(
            previous != "complete" for previous in statuses[:-1]
        ):
            errors.append(f"{name}: cannot advance before predecessor milestones complete")

    if statuses.count("in progress") > 1:
        errors.append("At most one milestone may be in progress")

    # Retired IDs remain valid historical references, never active exit criteria.
    retired: dict[str, set[str]] = {}
    revisions = documents["docs/history/REVISIONS.md"]
    for row in table_rows(revisions):
        if row[0] == "Retired ID" or all(re.fullmatch(r":?-+:?", cell) for cell in row):
            continue
        if len(row) != 4 or not re.fullmatch(r"M[1-5]-E[1-9]\d*", row[0]):
            errors.append("REVISIONS: expected retired ID, evidence kinds, original requirement, replacements")
            continue
        key, kinds_text, original, replacements_text = row
        kinds = {kind.strip() for kind in kinds_text.split(",")}
        replacements = {value.strip() for value in replacements_text.split(",")}
        if key in retired or key in criteria:
            errors.append(f"REVISIONS {key}: retired ID is duplicated or reused as an active criterion")
        if not original or not kinds or not kinds <= KINDS:
            errors.append(f"REVISIONS {key}: missing original requirement or invalid evidence kinds")
        if not replacements or not replacements <= criteria.keys():
            errors.append(f"REVISIONS {key}: replacement IDs must name current criteria")
        retired[key] = kinds

    for row in presence_rows:
        if len(row) != 3:
            errors.append(f"M1 {row[0]}: expected contract, scenarios, and current criteria")
            continue
        key, scenarios_text, criteria_text = row
        scenarios = {value.strip() for value in scenarios_text.split(",")}
        mapped_criteria = {value.strip() for value in criteria_text.split(",")}
        if not scenarios or not scenarios <= {f"S{number}" for number in range(26, 36)}:
            errors.append(f"M1 {key}: unknown or missing scenario mapping")
        if not mapped_criteria or not mapped_criteria <= criteria.keys():
            errors.append(f"M1 {key}: mappings must reference current acceptance criteria")

    latest_result: dict[tuple[str, str], str] = {}
    register = documents["docs/roadmap/EVIDENCE.md"]
    for cells in table_rows(register):
        if cells[0] == "Criterion" or all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        if len(cells) != 4:
            errors.append("EVIDENCE: each register row needs four columns")
            continue
        key, kind, artifact_text, result = cells
        if key not in criteria and key not in retired:
            errors.append(f"EVIDENCE: unknown criterion {key}")
        if kind not in KINDS or result not in {"pass", "fail", "pending"}:
            errors.append(f"EVIDENCE {key}: invalid kind or result")
        artifact = Path(artifact_text.strip("`"))
        resolved = (root / artifact).resolve()
        # Evidence references must stay portable and within this repository.
        if artifact.is_absolute() or not resolved.is_relative_to(root) or not resolved.is_file():
            errors.append(f"EVIDENCE {key}: missing or non-repository artifact {artifact_text}")
        # A newer failure or pending rerun invalidates an older passing claim.
        latest_result[(key, kind)] = result

    for key, (checked, required) in criteria.items():
        missing = {kind for kind in required if latest_result.get((key, kind)) != "pass"}
        if checked and missing:
            errors.append(f"{key}: checked without passing evidence for {', '.join(sorted(missing))}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1],
        help="Repository root; also allows isolated validation fixtures.",
    )
    args = parser.parse_args()
    errors = validate(args.root)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"Roadmap check failed: {len(errors)} issue(s).")
        return 1
    print("Roadmap structure and evidence references pass; behavior and evidence truth are not verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
