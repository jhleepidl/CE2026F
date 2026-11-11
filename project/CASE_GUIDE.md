# Create and submit your team's five cases

Each team contributes five travel situations to one common evaluation pool. Write
clear English requests and sources, keep their simulator fields consistent, and
show that each case has a successful tool sequence. Every team is evaluated on
the same accepted set, including all five cases from every team.

**You design the situations; the instructor reviews them before acceptance.**
Templates illustrate the format, not a required list of stories or solutions.
You may create new wording, document relationships, offers, events and combinations
of supported conditions. Keep the common tools, scoring rules and published limits.

Automatic checks verify the format and replay a supplied successful action sequence.
They do not judge whether a case is meaningful or whether its prose matches its
executable rules. Passing them does not automatically add a case to evaluation.
Review checks those meanings, information available before each decision,
realistic difficulty, and fair scope. Cases may need revision before acceptance.

At every leaderboard or final source submission, send **two ZIP files together**:
the three-file solver ZIP from `submit.py`, and the five-case ZIP from
`submit_cases.py`. Include the case ZIP even when its cases have not changed.

You may revise and submit your five cases together with your solver through
**December 7, 2026 (KST), inclusive**. From **December 8**, continue sending your
same accepted case content with each new solver submission. You may regenerate
witnesses for unchanged cases; this does not change the accepted case content.
The solver submission schedule and December 21 final source deadline are in the
[project README](README.md).

## Your five slots

Use the exact slot IDs and difficulty levels returned by
`framework.case_submission.team_slots`. The quotas are:

| Team | Slot 1 | Slot 2 | Slot 3 | Slot 4 | Slot 5 |
|---|---|---|---|---|---|
| `team1` | Basic | Basic | Reactive | Reactive | Forecast |
| `team2` | Basic | Basic | Reactive | Reactive | Forecast |
| `team3` | Basic | Basic | Reactive | Forecast | Forecast |
| `team4` | Basic | Basic | Reactive | Forecast | Forecast |
| `team5` | Basic | Reactive | Reactive | Forecast | Forecast |
| `team6` | Basic | Reactive | Reactive | Forecast | Forecast |

For example, `team3-4` is Team 3's fourth slot and must be Forecast. Six teams ×
five slots make **30 team-contributed evaluation cases**, ten per difficulty.
Revisions use the same assigned slots and do not add cases to the total.
The fixed Public examples and independent Hidden cases stay in place.

Your five cases are not published to other teams. You know your own cases, but
not the other teams' cases. Keep case files and witnesses out of public
repositories. They are part of the common official evaluation: **30 fixed
Public + 30 team-contributed + 60 independent Hidden cases, once each**.
Every solver is evaluated on the same set, including its author's five cases.

An invalid contribution remains unaccepted while you correct it before the
cutoff. Case validation adds no separate case-authoring grade. No API-cost
baseline is required with your cases.

## 1. Copy the templates into your slots

Run all commands below from `project/`, after the setup in [README.md](README.md).
The example uses `team1`; change `TEAM` and every later `--team team1` to your team.
The templates are starting points. Develop distinct situations by editing the
copied cases; changing only their names is not the purpose of this contribution.

```bash
python - <<'PY'
import copy
import json
from pathlib import Path
from framework.case_submission import team_slots

TEAM = "team1"
folder = Path("local_cases")
folder.mkdir(exist_ok=True)
entries = []
for slot_id, tier in team_slots(TEAM).items():
    template = Path("data/templates") / (tier + ".json")
    case = copy.deepcopy(json.loads(template.read_text(encoding="utf-8")))
    case["case_id"] = slot_id + "-travel"
    entries.append({"slot_id": slot_id, "case": case})
path = folder / "my_cases.json"
with path.open("x", encoding="utf-8") as handle:
    json.dump(entries, handle, indent=2)
    handle.write("\n")
print(path)
PY
```

The file contains exactly five wrappers of this form:

```json
{"slot_id": "team1-1", "case": {"...": "the complete copied case"}}
```

The abbreviated object above shows the wrapper only; keep the complete case from
the copy command. Use a distinct `case_id` for each case. Preserve your earlier
versions instead of overwriting them accidentally.

## 2. Edit a coherent situation

Start with one decision: an arrival obligation, a conditional allowance, a refund
exception, or a paid backup hold. Then add a clear interaction appropriate to the
slot's difficulty. [BENCHMARK.md](BENCHMARK.md) explains the operational behavior.

| If you change… | Keep these representations consistent |
|---|---|
| Spending authority | Request/source prose, `budget`, `operational_contract.budget_limit`, and any later amendments. |
| Required arrival | Client/registration prose, `deadline`, `operational_contract.arrival_deadline`, and transfers. |
| Refund terms | Per-ticket source text, `operational_contract.refund_terms`, offer references, and revised source versions. |
| Deposit or fare | Offer `hold_fee_usd`/`price`, source prose, spending feasibility, and the witness. |
| Access, carrier or mode | Applicable request/profile, structured fields, offers, and update notices. |
| Weather or a later change | Current warnings, event notice/time, source revisions, and the actual event `changes`. |
| Consent or waiver | Literal codes, evidence type, source version, cutoff, and witness arguments. |

The ordinary `budget` and `deadline` remain outer limits: the simulator uses the
smaller of each ordinary limit and its applicable operational expression. Do not
leave an old outer limit that contradicts a larger conditional allowance or a
later arrival obligation.

`operational_sources` links each spending, arrival and refund condition to its
readable source. Every changed operational condition needs an arrived notice and
a higher-version replacement of the linked source. A change to one field does
not silently replace unrelated conditions. Provide all facts needed for a sound
decision through the initial request, discoverable documents or arrived updates.

Case JSON is an **authoring definition**, including future events and executable
conditions. It never becomes an allowed runtime input to the solver. The solver
must obtain evidence from `observe`, `read`, `search` and the other published
tools. It may compile that observed prose into expressions and calculate locally.
Do not teach it a case-ID-to-answer table or feed it the authoring definition.

### Expressions and bounds

The three operational programs return a total dollar ceiling, a required client
arrival clock minute, and retained cancellation dollars for each ticket.
A refund result of `null` means cancellation is forbidden. Supported expressions
include `if`, comparisons, `and`/`or`/`not`, `add`/`sub`/`min`/`max`, and `exists` or
`minimum` over observed offers or holds. There are no submitted Python functions,
network calls or custom grading functions. See the templates and
[expression definitions](framework/operational_expressions.py) for exact forms.

The `offers` pool means current unheld inventory that is still on sale, plus the
candidate being considered when it has a valid live hold. That held candidate
still counts after public sales close. Other held tickets belong to `holds`,
not automatically to `offers`. Explain this distinction in a source whenever an
approval depends on the cheapest available quote or on an alternative hold.
Do not write prose whose ordinary meaning disagrees with these pool rules.

For example, a source that allows USD 145 for flight and USD 105 for another mode
has this spending expression:

```json
{
  "op": "if",
  "when": {"op": "eq", "left": {"var": "candidate.mode"}, "right": "flight"},
  "then": 145,
  "else": 105
}
```

Use `state.now` for virtual action-completion time. `meeting_arrival` means
terminal arrival plus current transfer; it is a different clock. Conditions may
use supported candidate/booking facts and observed financial/weather state.
Inside a quantifier, `item` means an offer or live hold being examined.

| Limit | Published bound |
|---|---|
| Case horizon | Exactly 36 virtual minutes. |
| Offers / documents / events | 1–24 offers, at most 16 documents, at most 8 ordered events. |
| Case size / prose | At most 100,000 UTF-8 bytes per case; at most 6,000 characters per source or notice; 30,000 total prose characters. |
| Clock arrival / transfer | Arrival clock minute 0–1439; each mode's transfer 0–180 minutes. |
| Holds / deposits | Hold duration 1–36 minutes; deposit and base cancellation fee between zero and the fare price. |
| Expressions | At most 128 nodes, depth 12, and two nested quantifiers; finite numeric literals within ±1,000,000. |
| Witness | At most 128 steps and 256 tool actions; a batch may list at most 12 actions, scheduled through the same three tool slots. |
| Case ZIP | Exactly `cases.json`, `witnesses.json`, `CASE_MANIFEST.json`; each file at most 2 MB. |

Keep the required `hotel-terms`, `hotel-bulletin`, `traveler-profile` and
`transport-guide` documents. Use the current project version, supported modes
(`flight`, `train`, `coach`), and the assigned difficulty. Full field validation
is defined in [world_factory.py](framework/world_factory.py).

Use clear, realistic travel conditions from the
[supported condition combinations](BENCHMARK.md#supported-condition-combinations).
Keep the difficulty appropriate to the assigned slot. A new case should involve
a meaningful decision, not just different names or amounts. Do not use a team's
identity, private information, arbitrary secret rules or confusing nonsense as
travel conditions. Required facts must be available through the published tools
before the decision that needs them.

## 3. Inspect and run your five cases

```bash
python inspect_case.py --local-cases local_cases/my_cases.json --case 1
python run.py --local-cases local_cases/my_cases.json --output runs/my_cases_01
```

Inspection uses no API calls. The local run uses your current `solution/` and may
make paid calls according to its configuration; the usual call and spending
guards apply. It runs each case once and records `results.json`, `cases.csv` and
`report.html`. Its outcome /90 is a diagnostic, not an official leaderboard grade.

Inspect failures and actual actions. To package with `--report`, the report must
contain a complete successful episode for each of your five cases. If your solver
fails, improve it or correct an inconsistent/unworkable case, then run again into
a fresh directory such as `runs/my_cases_02`. You may instead supply a successful
action sequence with `--witnesses`, as described below. Acceptance does not require
the provided starter solver to solve your cases.

## 4. Package both ZIPs

```bash
python submit_cases.py --team team1 --cases local_cases/my_cases.json --report runs/my_cases_01/results.json --output submissions/cases_01.zip
python submit.py --output submissions/solution_01.zip
```

Use the report from your successful current run. `submit_cases.py` matches the
exact cases, extracts their recorded tool actions as witnesses, checks the case
structure, and replays all five witnesses before writing the ZIP. Packaging makes
**zero new API calls** and requires complete success. A written
`expected_success` flag cannot substitute for successful replay.

If you edit cases, rerun them before packaging. For unchanged cases, reuse the
existing valid case ZIP or package a later successful report. Advanced users may
replace `--report` with `--witnesses local_cases/witnesses_01.json` to supply
witnesses directly; the same checks apply. Template `*_witness.json` files show
the action format but are not automatically valid for edited cases.

Email `submissions/solution_01.zip` and `submissions/cases_01.zip` together to the
existing course submission address. The source ZIP contains only `config.py`,
`prompts.py`, `policy.py` under `solution/`, plus its generated manifest. The case
ZIP contains the five cases, witnesses and its generated manifest. Do not add
keys, framework files, run reports or extra solver modules.

From December 8, keep attaching the same accepted cases with every solver ZIP.
Do not silently revise case content after the cutoff. Regenerating a witness does
not authorize changing a case. Every official leaderboard entry covers the
complete common evaluation set. An LLM, multiple agents or a minimum number of
API calls is not required; valid zero-API methods receive the same outcome checks
and published efficiency formula.
