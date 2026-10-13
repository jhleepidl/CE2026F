# Public data and case inspection

The project supplies **nine dev cases and 24 public cases**. Dev has three cases
per difficulty; Public has eight per difficulty. Final grading also includes
24 hidden evaluation cases. The same tools and 100-point rubric apply to every team.

Start with [three readable examples](examples.md). For the kinds of changes your
assistant should handle, read the [benchmark guide](../BENCHMARK.md). It also
explains how to make optional local tests from an existing case.

## What is in this folder?

| File | Contents |
|---|---|
| [`catalog.jsonl`](catalog.jsonl) | 33 records: one per dev/public case, with split, case ID, difficulty, initial request and initial source titles. |
| [`examples.md`](examples.md) | One Basic, one Reactive and one Forecast example, showing actual requests, read sources and offers. |
| [`MANIFEST.json`](MANIFEST.json) | Data version and file checksums. |

The catalogue contains initial inputs, without future event tapes, grading
answers or solution plans. The public case definitions are readable in
[`framework/fp_cases.py`](../framework/fp_cases.py). During a solver run, use only
current observations and tool replies; do not look up future events or answers
from a case definition.

## Inspect actual inputs with no model calls

Run from `project/`:

```bash
python inspect_case.py --split dev
python inspect_case.py --split public --tier forecast --case 1 --output runs/preview
```

The first command lists cases. The second shows the initial request, documents
returned by read tools and available offers. A row number refers to the current
split/tier list, starting at 1; you can also supply a case ID. `preview.md` is
readable and `preview.json` retains actual tool replies. Reads advance virtual
time, so each reply shows when it completed. Inspection needs no API key, makes
no bookings and gives no model-performance score. Solver runs start fresh.

## Create your own optional local tests

```bash
python inspect_case.py --split dev --case 1 --export-case local_cases/example.json
python inspect_case.py --local-cases local_cases/example.json --case 1
python run.py --local-cases local_cases/example.json --output runs/local_01
```

The export copies one existing public case into a JSON list. It is a local test
authoring file, so it includes the simulator definition and future event schedule.
Keep those definitions out of solver inputs. Read the
[authoring instructions](../BENCHMARK.md#make-your-own-local-tests) before changing
facts. Local test files are ignored by Git and are not submitted or officially
graded. They may be created freely alongside the three submitted solution files.

Dev and local runs show outcomes /90 and actual API cost. Only the complete
24-case Public run, twice per case, receives a provisional /100 public score.
Final grading runs one frozen submission on all 96 public-plus-hidden episodes.

Public cases and self-authored tests can be overfit. Use the benchmark guide to
cover different behaviors and inspect failures on each difficulty. Names and
wording can change within the published contract; hidden cases add no secret
criterion. No finite authored bank proves broad generalization, and valid
numerical or symbolic solutions remain allowed.
