# M1 Handoff

## Current state

M1 remains `in progress`. The conversation-first specification has 25 scenarios
and a matching walkthrough. All M1 acceptance criteria remain unchecked; no
owner acceptance or runtime validation is claimed. M2–M5 remain pending.

## Latest work: 2026-09-17

- Clarified M1-E2/E3/E4 as `(document, owner)`: the material must exist and
  the owner must accept the corresponding semantics/scope. One explicitly
  scoped owner review can cover all four M1 criteria. The owner's feedback
  approved this clarification, not the milestone's behavior specification.
- Made table padding, optional trailing pipes, common heading dash separators,
  and ordinary criterion/status spacing editorial rather than acceptance gates.
  Scenario identity, uniqueness, phase order, and evidence kinds remain strict.
- Added persistent checker regression tests in `scripts/test_check_roadmap.py`.
- Addressed M1-E2/E3/E4 documentation support by adding an execution contract,
  stable acceptance IDs and evidence kinds, a shared evidence register, and
  a local structural checker. These additions are awaiting review, not passes
  for those criteria.
- The owner's request was to assess and strengthen the documents so other AI
  assistants can follow the main direction. It did not approve M1's scenarios
  or authorize starting M2 implementation.
- Existing Roadmap glossary and M2a–M2d delivery checkpoints remain unchanged.
- The checker only verifies structural consistency and referenced artifacts;
  it cannot authenticate owner statements or judge live conversation quality.

## Verification

- `python3 scripts/check_roadmap.py`: passed on the current documents; all
  34 criteria remain unchecked and the evidence register remains empty.
- `python3 -m unittest discover -s scripts -p 'test_*.py'`: 11 tests passed,
  covering formatting tolerance, exact IDs, prerequisite order, combined
  document/owner requirements, shared review artifacts, and superseded passes.
- On the earlier checker revision, an isolated temporary-fixture run exercised
  ten cases: current documents,
  mismatched status, premature M2 start, checked criteria without evidence,
  document evidence substituted for owner review, missing artifacts, a lost
  scenario row, valid structural document evidence, a newer failure overriding
  an older pass, and a broken link. All produced the expected result. Synthetic
  evidence existed only in temporary fixtures and was not copied into this repo.
- `git diff --check`: passed. Application, live, and integration tests are not
  run: the repository has no MVP implementation yet.

## Next smallest action

Obtain or record the owner's actual review of S11–S25 and the retained S1–S10,
especially S20 nonresponse and S15/S25 mute versus cancellation. Separately
include the revised walkthrough, open-question dispositions, and roadmap scope
in that review; separate approval messages are not required. Store genuine
acceptance evidence for each covered ID before checking M1 criteria.

Routine in-scope review and document corrections can continue. Do not implement
M2 or treat another AI's positive review as the owner's acceptance. Once M1
criteria are met, synchronize phase status and start with M2a; select and
record the concrete channel/source/model/limits under M2's scope.
