# CE2026F Final Project

## Travel planning with dynamic replanning

Build an assistant that keeps a trip workable as requests, weather and booking
options change. Read the right evidence, update memory, make authorized bookings
and verify the result. Travel outcomes and API cost produce a score out of 100.
You may use one or several model roles, ordinary Python planning, or a combination.

**Version: `travel-2026f-v10`.** The update adds conditional spending permission,
arrival requirements, refund terms and paid reservations. Each team also
contributes five evaluation cases. [Updating an existing solver](#updating-from-v9)
explains how to keep your work.

**Final source deadline: December 21, 2026 (KST).** The exact time
will be announced separately. All final presentations are **online via
Zoom**, on the course presentation schedule.

## Start here

Use Python 3.11 or later. From this repository:

```bash
cd project
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, use `.venv\Scripts\Activate.ps1` and
`Copy-Item .env.example .env`. Put your own already distributed course API key
in the local `.env` file:

```dotenv
OPENAI_API_KEY=PASTE_YOUR_KEY_HERE
```

Never share the key. `.env` and generated runs/submissions are ignored by Git.

```bash
python run.py --offline
python inspect_case.py --split dev --case 1
python run.py --split dev --limit 2 --output runs/setup_check
```

The first two commands make no model calls. The third is a **paid experiment**.
Open `runs/setup_check/report.html` to see the outcomes, actions and API usage.
Use a fresh output directory for each run.

## Your solver and five cases

Your work has two parts: edit the three solver files below, and create five
travel cases in your own JSON file under `project/local_cases/`. The
[case guide](project/CASE_GUIDE.md) provides templates and the packaging command.

| File | Your choices |
|---|---|
| [`project/solution/config.py`](project/solution/config.py) | Model, supported settings, refresh and policy budgets. |
| [`project/solution/prompts.py`](project/solution/prompts.py) | Instructions and role prompts. |
| [`project/solution/policy.py`](project/solution/policy.py) | Routing, memory, planning and the agent loop. |

These are the **only submitted Python files**. Put helpers inside them. Read the
framework freely, but keep the tools, accounting, evaluator, runners and supplied
benchmark data unchanged. Use the standard library and the provided requirements;
extra code files or assets are not installed from a submission.

The starter provides a working loop, source memory, a numerical planner and API
logging. It deliberately keeps its first interpretation unless you enable
refresh. You can improve this loop or replace it. Memory lasts for one trip; each new
case execution starts fresh. See the
[student guide](project/README.md#2-your-files-and-the-provided-scaffold) for memory
rules and the provided components. All model calls use the supplied API wrapper,
which supports Responses and Decisions. AI-coder assistance is allowed.

## Test and submit

Run from `project/`:

```bash
python run.py --split dev --output runs/dev_01
python run.py --split public --output runs/public_01
python submit.py --output submissions/team_solution.zip
```

Dev has nine cases. A complete local Public run evaluates 30 cases twice and
shows a development score. **Only official grading contributes to the
leaderboard.** We run your submitted solver on this common set, once per case:

| Official evaluation set | Cases | Who can see them before grading? |
|---|---:|---|
| Fixed Public examples | 30 | Everyone, in this repository. |
| Team-contributed cases | 30: five per team | Each team knows its own five; other teams do not receive them. |
| Independently prepared Hidden cases | 60 | Not released to teams. |
| **Total** | **120** | The same evaluation set is used for every team. |

At every leaderboard or final submission, email **two ZIPs** to the existing
course submission address:

1. Your solver ZIP, created by `submit.py`.
2. Your five-case ZIP, created using the [case guide](project/CASE_GUIDE.md).
   Include it even when your cases have not changed.

Contributions **do not change the fixed Public set** or the independently prepared
Hidden cases. Keep case files and witnesses out of public repositories. All cases
use the [published benchmark scope](project/BENCHMARK.md). Scores are compared
only on the same common evaluation set. Revisions replace assigned contribution
slots and do not accumulate.

## Score and leaderboard

| Criterion | Maximum |
|---|---:|
| Usable arrival | 40 |
| Current requests: spending, preference, accessibility and carrier | 20 |
| Hotel fee waiver | 10 |
| Safe actions | 10 |
| Reliable handoff | 10 |
| API efficiency | 10 |

The outcome criteria are averaged over cases. API efficiency compares the cost
of all model calls in the official evaluation with a common allowance of
**$0.04814950**. Cached input uses the ordinary input price for grading; actual
cost estimates are shown separately. Earlier development costs are not added to
the official evaluation. See the [score formula and examples](project/README.md#7-understand-the-100-point-score).

The leaderboard will be a shared Google spreadsheet; the link will be added
here later. It shows the total, criterion and difficulty scores, success and
costs. Final grades use your final submitted source, not your rank or best past
entry. The maximum remains 100, with no points for a particular architecture.

| Date in 2026, Korean time | What happens |
|---|---|
| Through December 7, inclusive | Submit or revise your five cases with each solver submission. |
| From December 8 | Attach the same accepted cases while improving your solver. |
| Through December 13 | At most one leaderboard grading request per team per calendar day. |
| December 14–19, inclusive | No daily limit on leaderboard grading requests. |
| From December 20 | Interim leaderboard grading requests are closed. |
| December 21 | Final source submission is due; exact time announced separately. |

December 7 is the case-content cutoff, not a single submission day. Cases
received by then may finish review later. Any necessary correctness fixes will
be explained and applied consistently to the common evaluation set.

## Updating from v9

Back up your three solution files, get the new release, then restore those files.
Run the offline check and test Dev again. The function interfaces stay the same,
but a fixed budget number or a base fare label may no longer describe all current
conditions. Source discovery before reading remains required.

## Reference guides

Start with this README and a small Dev run. Use the guides below as references
while improving your solver; follow the case guide when preparing your five cases.

- [Student guide: memory, tools, API settings, score and submission](project/README.md)
- [Benchmark: supported conditions and useful tests](project/BENCHMARK.md)
- [Case guide: create, validate and package your five cases](project/CASE_GUIDE.md)
- [Optional data inspection and examples](project/data/README.md)

`CE2026F_A3_Documents.zip`, when present, belongs to Assignment 3 and is not needed
for this project.
