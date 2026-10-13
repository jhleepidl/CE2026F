# Travel planning with dynamic replanning

Build a travel assistant that interprets changing requests and sources, makes
approved bookings, repairs them when needed, and verifies the trip through
handoff. Use the supplied dev cases to begin, then make optional local tests
for the kinds of failures described in the benchmark guide. Final grading reruns
your submitted source on public and hidden cases for a score out of 100.

**Final submission: December 21, 2026 (KST).** The exact deadline time will be
announced separately.

The starter is runnable. You can begin with prompts and configuration, then
extend routing, memory or the action loop as your experiments identify failures.

## 1. Install and check the setup

Use Python 3.11 or later. From the repository root:

```bash
cd project
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Windows activation: `.venv\Scripts\activate`, or
`.venv\Scripts\Activate.ps1` in PowerShell. PowerShell can copy the template with
`Copy-Item .env.example .env`.

Open `.env` in your editor and replace the placeholder with your own course API
key, which has already been distributed to you. Keep it local:

```dotenv
OPENAI_API_KEY=PASTE_YOUR_KEY_HERE
```

`run.py` reads `project/.env`; an existing `OPENAI_API_KEY` environment variable
takes precedence. Do not put a real key in a Python file or commit it.

Check the simulator without a model request:

```bash
python run.py --offline
```

It prints `Offline simulator inspection: zero API calls; no model grade.` and
shows a source change as virtual time advances. This confirms local imports and
tools work; it does not measure model quality.

Then make a small paid setup check:

```bash
python run.py --split dev --limit 2 --output runs/setup_check
```

Open `runs/setup_check/report.html` in a browser. These first two basic cases are
a setup check; run all nine dev cases to see dynamic situations.

Every paid run has a 1000-call / estimated USD 2 guard, a 180-second request
timeout and zero automatic retries. A rerun makes new paid calls. Always choose
a fresh output directory so earlier evidence is preserved.

## 2. Know which files to edit

```text
project/
  solution/
    config.py             EDIT: model/settings and policy choices
    prompts.py            EDIT: task and role instructions
    policy.py             EDIT: routing, memory, planning and agent loop
    __init__.py           Keep unchanged
  framework/              READ: common tools, world, public cases and evaluator
  run.py                  Keep unchanged: dev/public and optional local runner
  inspect_case.py          Keep unchanged: view observed case data; no API calls
  BENCHMARK.md            READ: task variations and local test authoring
  data/                   READ: public case catalogue and examples
  local_cases/            OPTIONAL: your own test JSON files; ignored by Git
  submit.py               Keep unchanged: submission packager
  RELEASE_MANIFEST.json   Keep unchanged: release hashes and edit allowlist
  requirements.txt        Keep unchanged: runtime dependencies
  .env.example            Placeholder template
  .env                    Your local key; ignored by Git
  runs/                   Generated reports; ignored by Git
  submissions/            Generated source ZIPs; ignored by Git
```

**Your submitted implementation is exactly three files:**

You may change any of these files; changing all three is not required.

| File | What you can change |
|---|---|
| [`solution/config.py`](solution/config.py) | Model and supported controls, architecture, context refresh, concurrency, routing threshold and policy budgets. |
| [`solution/prompts.py`](solution/prompts.py) | `PROJECT_PROMPT` and `ROLE_PROMPTS`: how evidence and previous fields should be interpreted. |
| [`solution/policy.py`](solution/policy.py) | `route()` and `solve()`, plus any extra functions/classes needed by your design. |

Keep submitted helper functions and classes inside these files. Use the Python
standard library, public framework helpers and packages in `requirements.txt`.
Additional packages, helper modules, local assets and test JSON are not installed
or copied from your submission. You may freely create local test JSON files in
`local_cases/`; those files are not submitted. Read the shared implementation
freely while keeping it unchanged.
Final grading runs the three submitted files under the published tools and
evaluation rules.
Changes outside the allowlist are review/rerun candidates, not automatic deductions.

The starter already reads sources, keeps local state, compares numeric options,
books, checks status and monitors the trip. It delegates that working loop from
`solve()`. You may keep it and improve its context handling; a full rewrite is
optional. Its `REFRESH_CONTEXT=False` leaves model-extracted fields frozen after
the first interpretation, giving you a concrete place to begin.

The two useful starter architectures are `hybrid_single` (one combined
interpreter) and `hybrid_multi` (combined or separately scoped calls). They use
the same three tool slots and numeric planner. Concurrent model requests can
reduce wall-clock waiting; they do not advance or save virtual trip minutes.

In the supplied hybrid, these editable prompts have different paths:

| Prompt | When it is used |
|---|---|
| `PROJECT_PROMPT` | Appended to every hybrid extraction request. |
| `ROLE_PROMPTS["transport"]`, `["hotel"]`, `["traveler"]` | Used for separate scoped calls in non-Basic `hybrid_multi` episodes when the number of requested domains is at least `ROUTE_THRESHOLD`. |

Basic always uses the provided combined extraction instructions plus
`PROJECT_PROMPT`. `hybrid_single` and combined fallback calls use that same
combined path, so editing only `ROLE_PROMPTS` does not change those requests.
Inspect the saved API request's role and instructions to check which prompt ran.

## 3. Understand the travel task

The lead traveler's outbound was cancelled. Arrange a replacement to a fictional
client meeting while preserving the existing hotel and colleague's return.
Respect the latest meeting time, transfers, spending approval, feasible mode
preference, accessibility and carrier restrictions. Remove the pending USD 55
hotel fee using the current evidence procedure.

An instruction for the colleague or a later journey is not automatically a rule
for this outbound. New instructions may lift old restrictions as well as add them.
The spending check happens when `confirm` commits a booking. It uses the limit
then in effect, transport spending left after refunds and any pending hotel fee.
A hold does not keep an older spending approval. A later budget reduction does
not invalidate an earlier approved purchase. Meeting, access and carrier checks
use the latest requirements at handoff, so those updates can make an earlier
booking unsuitable. Outbound approval never authorizes changing the protected
bookings.

| Difficulty | What changes | Your planning responsibility |
|---|---|---|
| Basic | No later external notices. | Choose an eligible itinerary, resolve the hotel fee and verify completion. |
| Reactive | Meeting, budget, preference, evidence, inventory, transfers or traveler scope. | Confirm a first outbound by minute 14, then update and repair through handoff. |
| Forecast | Reactive constraints plus revised weather advisories, fare contracts and recovery windows. | Confirm by minute 12, preserve feasible recovery, and handle later observed changes. |

Basic permits immediate verified handoff. Reactive and forecast cases monitor
through virtual minute 24. Every episode finishes by minute 36. Fee cutoffs and
offer windows can be earlier, so read the actual case requirements.
There is no reward for checking every minute; monitor when it preserves the
service obligation and time for a useful repair.

Search results state the fare contract:

- `locked`: cancellation and exchange are rejected after confirmation.
- `fee`: approved cancellation refunds the paid fare minus `cancel_fee_usd`.
- `flexible`: approved cancellation refunds the whole fare.

Cancel your existing replacement before confirming another. Retained fare fees
remain part of spending even after the ticket is replaced. A valid hold protects
its quoted inventory until the hold deadline. Quotes also state when they open
and close; do not assume a later alternative remains available indefinitely.

A weather forecast is uncertain evidence for a stated traveler, journey and mode.
Its percentage and possible additional duration are not an observed delay.
Later reports can revise the watch or report what actually happened. Current
search and booking arrivals already include observed physical delays; do not add
them twice. Authored false alarms and disruptions are not an empirical weather
calibration dataset. A valid robust hedge is allowed.

## 4. Use the supplied tools and API

Your `solve(world, api, config, route_fn)` receives two controlled interfaces:

| Interface | Purpose |
|---|---|
| `world.observe()` | Current time, notices, source catalog/versions, bookings, holds and spending; no time advance. |
| `world.call(tool, **arguments)` | Run one local tool. |
| `world.batch(actions)` | Run independent tools using three common slots. |
| `api.json(config["model_settings"], instructions, payload, schema, label)` | Make a schema-constrained model request and record its usage/cost. |
| `api.usage()` | Read this episode's measured model usage. |

All model calls must go through `api.json`. Do not create a separate client or
bypass the usage ledger. The course adapter accepts these model settings:

| Model | `EFFORT` values | `VERBOSITY` | Sampling controls |
|---|---|---|---|
| `gpt-5.6-luna` | `none`, `low`, `medium`, `high`, `xhigh`, `max` | `low`, `medium`, `high`, or `None` | Only with `EFFORT="none"`. |
| `gpt-5.4-nano` | `none`, `low`, `medium`, `high`, `xhigh` | `low`, `medium`, `high`, or `None` | Only with `EFFORT="none"`. |
| `gpt-5-mini` | `minimal`, `low`, `medium`, `high` | `low`, `medium`, `high`, or `None` | Keep both `None`. |
| `gpt-5-nano` | `minimal`, `low`, `medium`, `high` | `low`, `medium`, `high`, or `None` | Keep both `None`. |
| `gpt-4o-mini` | `None` | `None` | Supported. |

The classroom output cap is 16–4096 tokens. Use `None` for optional verbosity or
sampling controls where the table permits it; choose a listed `EFFORT` value.
The string `"none"` is a reasoning-effort value for the first two models. Where
sampling is supported, set `TEMPERATURE` (0–2) or `TOP_P` (0–1), not both.
Unsupported combinations fail locally before a paid request. See
[`framework/settings.py`](framework/settings.py) for the exact adapter and
accounting prices. Compare measured task outcomes and cost when changing models.

| Tool | Virtual duration | Main arguments and result |
|---|---:|---|
| `search` | 2 | Current offers with IDs, prices, arrivals and fare terms. |
| `read` | 2 | `id`: catalog source ID; returns its text and version. |
| `inquire` | 3 | `topic`: `traveler`, `hotel` or `transport`; returns current clarification. |
| `claim` | 2 | `topic`, `code`, `version`: current waiver evidence; must complete strictly before cutoff. |
| `hold` | 1 | `id`: offer ID; returns a hold ID and expiry. |
| `confirm` | 2 | `id`: hold ID, `code`: outbound approval, `key`: stable request key. |
| `status` | 1 | `key`: inspect confirmation outcome before trying a new booking. |
| `cancel` | 2 | `id`: your replacement booking ID, `code`: its approval. |
| `wait` | N | `minutes`: positive virtual minutes to advance. |
| `finish` | 0 | Verified handoff; cannot finish before the case's handoff time. |

See [`framework/fp_world.py`](framework/fp_world.py) for exact contracts and
[`framework/fp_agents.py`](framework/fp_agents.py) for working calls using
`travel_action(...)`. Read `hotel-terms` and follow its bulletin link; inspect the
current `transport-guide`, `traveler-profile`, and applicable `weather-forecast`.

Tool results are dependencies: obtain a hold ID before confirming it. A missing
confirmation reply can follow a committed booking; inspect `status` with the
same key. Reusing the identical key and payload is idempotent. A different key
can create a duplicate logical booking. These are simulated travel operations;
tools do not contact real travel providers or make real payments.

External changes advance with virtual tool time. API/CPU wall time does not
advance the virtual clock. Each team has an isolated world with the same seeded
event tape for a given case. Do not use future event definitions, `_spec`, `_rules`,
evaluator answers or case-ID lookup tables to choose actions. Public case code is
available for inspection; the solver still operates through the observed interface.

## 5. Manage context and memory

The simulator owns bookings and finances. A local dictionary cannot change a
reservation; only an approved tool action does that.

The supplied hybrid creates these stores inside each episode:

| Store | Contents |
|---|---|
| `documents` | Read source text and version, keyed by source ID. |
| `state` | Interpreted meeting, budget, approval, preference, access, carriers, transfers, waiver and forecast fields; observed net spending. |
| `memory` | Routing metadata: previous interpretation time/revision and pending hotel work. |
| `options` | Current numeric search results. |

Model inputs explicitly contain selected sources, relevant notices and previous
fields. There is no implicit conversation memory or required database. Diagnostic
traces are not automatically included in the next model request.

With `REFRESH_CONTEXT=False`, the supplied hybrid skips later model extraction,
while live observations, coded source rereads and financial updates still occur.
`True` enables selective reinterpretation. New extracted fields overwrite matching
entries; the scaffold does not provide a general conflict resolver, per-field
provenance/confidence or automatic forgetting.

`route(observation, memory)` returns any needed domains: `transport`, `hotel`,
`traveler`. In the supplied loop it receives a **copy of routing metadata**, not
the full `state` or `documents`; edits to that argument do not persist.

To design another memory representation, merge policy, compression strategy or
action loop, replace `solve()` inside `solution/policy.py`. Initialize episode
memory inside `solve()`; module globals are not reset between episodes. Return
a JSON-serializable dictionary, for example `{"traces": [], "working_memory": memory, "context": state}`. Call
`world.call("finish")` after the required monitoring and verification. Wait for
all model calls you started to complete before returning from `solve()`; do not
leave background requests running. A full rewrite is optional, and memory format
itself is not graded.

## 6. Improve with visible experiments

Read [BENCHMARK.md](BENCHMARK.md) for the scenario families, what can vary and
how to author useful local tests. The supplied cases are:

| Set | Distinct cases | Repeats | Purpose |
|---|---:|---:|---|
| Dev | 9, three per level | 1 | Setup and small experiments. |
| Public | 24, eight per level | 2 | 48 episodes; provisional public score /100. |
| Hidden evaluation | 24, eight per level | 2 | Final evaluation with Public. |
| Your local cases | You choose | 1 | Optional diagnostic tests; no official grade. |

The [data guide](data/README.md) and [three examples](data/examples.md) show
readable input data. [`data/catalog.jsonl`](data/catalog.jsonl) lists the initial
requests and source titles for all 33 student-visible cases. Inspect a case
without an API key:

```bash
python inspect_case.py --split dev
python inspect_case.py --split public --tier forecast --case 1 --output runs/preview
```

Without `--case`, inspection lists matching cases. Use a case ID or the number
in that list, starting at 1. Inspection prints the actual request, read source
text and search offers, with their observation times. Tool reads advance virtual
time. It makes no model calls and does not reveal the future event tape or a
solution. Solver runs start fresh and read their own evidence.

1. Try one controlled context-refresh experiment:

   ```bash
   python run.py --split dev --tier reactive --limit 1 --output runs/reactive_frozen_01
   ```

   Keep the other starter values and change only `REFRESH_CONTEXT` in
   `solution/config.py` from `False` to `True`. Then run the same case again:

   ```bash
   python run.py --split dev --tier reactive --limit 1 --output runs/reactive_refresh_01
   ```

   Open both `report.html` files. Compare the later traveler notices, interpreted
   meeting time, final booking, outcome /90 and both cost estimates. This tests whether
   refreshed interpretation helps this case. One pair of model runs does not
   establish a stable improvement; there is no promised result.

2. Read the report in this order:

   - Start with **Criterion scores**, **Scores by difficulty** and **Episode
     results**. A failed episode can still earn useful partial credit.
   - Expand the failing case's **tools and solver context**. Compare `checks`
     with the actual `history` and the fields returned under `solver`.
   - Expand **Every API request, actual reply and token usage** for the exact
     request role, prompt, reply and cost estimates. Check that the prompt you edited ran.
   - Expand **Outcome components and usage** for aggregate success, token usage and both cost estimates.

   Run all dev cases before judging the design:

   ```bash
   python run.py --split dev --output runs/dev_01
   ```

   Then improve one part at a time: when to refresh, which evidence each role
   gets, prompt length, model settings, or how new facts replace old state.
   More advanced choices include fact/source tracking, conflict handling,
   forecast/fare planning and a custom loop. Compare each difficulty and API
   cost. Keep working scaffolding until an observed failure calls for a change.

3. If helpful, make your own local test by copying one supplied case:

   ```bash
   python inspect_case.py --split dev --case 1 --export-case local_cases/example.json
   python run.py --local-cases local_cases/example.json --output runs/local_01
   ```

   This exports one existing public case as a JSON list. Edit a copy using the
   [local authoring guide](BENCHMARK.md#make-your-own-local-tests), then inspect
   and run it. New wording is a useful first change. Changes to facts also need
   matching text, document values and event changes. Local test files are optional
   and are not submitted. Keep the official framework and datasets unchanged.

4. Keep some of your local cases aside while improving the solution. Test the
   same source and settings on those cases before changing them again. A small
   authored test set can expose failures but does not prove broad generalization.

5. Run the complete Public bank when ready:

   ```bash
   python run.py --split public --output runs/public_01
   ```

Dev, local and filtered/subset runs show mean outcomes /90, criterion and
difficulty results, full success, actual token usage, grading cost and estimated
API cost. They do not apply the
full Public bank's cost reference to a different case set. Only a complete,
unfiltered Public run receives the provisional /100 public score. Use `--tier`
or `--limit` for smaller diagnostics.

Runs preserve the source snapshot, configuration, actual replies, tool history,
tokens and estimated cost. `results.json`, `cases.csv` and `report.html` are
created evidence, not code to edit or required submissions. Choose a fresh output
directory for each run. Rerunning a model evaluation makes new paid calls.

If an API timeout, connection, authentication or budget interruption occurs, keep
the partial record and resolve the cause before a fresh run. Unknown usage/cost
blocks a complete score. There is no automatic paid retry or engine fallback.
A real API interruption is different from the simulated provider's missing
confirmation reply.

## 7. Understand the 100-point score

The evaluator checks state and history and accepts any itinerary that meets the
published contract:

| Criterion | Points | What is checked |
|---|---:|---|
| Usable arrival | 40 | One confirmed outbound, eligible under current access/carrier rules, reaches the latest meeting including transfers. |
| Current requests | 20 | Five each: approved spending including retained fees, feasible preferred mode, required access, permitted carriers. |
| Hotel waiver | 10 | Applicable evidence/version accepted before cutoff while preserving the room. |
| Safety | 10 | Authorized actions, protected bookings preserved, no duplicate outbound. |
| Reliable handoff | 10 | First confirmation on time, confirmation outcome verified, monitoring and handoff complete. |
| API efficiency | 10 | Grading cost relative to a fixed recorded benchmark, with cached input charged at the regular input rate. |

Average the first five criteria across all episodes to get `O`, out of 90.
For positive solver **grading cost** `S` and fixed benchmark **grading cost** `B`:

```text
score = min(100, O + 10 * min(1, B / S))
```

A valid zero-API solution receives the full 10 efficiency points. Every model
request counts, including specialists and repeated attempts. Local numerical
search is free.

For grading, count **all input tokens, including cached tokens**, at the model's
published uncached-input rate, and output tokens at its output rate. Sum this
amount across every request. The same calculation applies to the solver and
recorded benchmark. This keeps cache hits from changing a score when two runs
use the same tokens.

```text
grading cost per request =
    (all input tokens × uncached-input price per million
     + output tokens × output price per million) / 1,000,000
```

| Evaluation | Fixed grading-cost reference B | Recorded API cost estimate |
|---|---:|---:|
| Public: 48 episodes | USD 0.01917000 | USD 0.00827514 |
| Final Public + Hidden: 96 episodes | USD 0.03851960 | USD 0.01655132 |

The grading cost is a common comparison measure, not an actual invoice. Reports
also retain cached-token usage and the API cost estimate with cache discounts.
That separate estimate shows the cost of the observed run but does not determine
the efficiency score. See [`framework/settings.py`](framework/settings.py) for
the accounting rates and [`framework/fp_baseline.py`](framework/fp_baseline.py)
for recorded aggregate metadata. The benchmark does not run again during your
evaluation.

For example, outcome `O=80` and grading cost `S=2B` earn `80+5=85/100`. Grading
cost at or below B earns all 10 efficiency points. Reducing prompt length or
unnecessary calls can reduce both cost measures; receiving a cache discount
reduces only the API cost estimate.

All three difficulty levels use this same rubric and have equal outcome weight.
The leaderboard displays each level's contribution to the total:

```text
Basic /30    = mean Basic outcome /90 divided by 3
Reactive /30 = mean Reactive outcome /90 divided by 3
Forecast /30 = mean Forecast outcome /90 divided by 3
Total /100   = Basic + Reactive + Forecast + API efficiency /10
```

The detailed report also shows each level's outcome /90 and complete-success
count. API efficiency is calculated once over the whole scored bank; it is not
added separately to each difficulty. Criterion scores are another breakdown of
the same total, not additional points. The four request subcriteria divide the
20 request points; they do not add another 20. Arrival means a usable itinerary,
so an access/carrier violation can lose arrival credit and its request subcriterion.
This overlap is part of the published contract.

Scores are displayed to two decimal places and stored without that rounding.
The score scale does not make the sample more statistically precise. The current
scoring version is `travel-score-2026f-v3-100`; compare scores from the same bank
and scoring version. Recorded benchmark tables explicitly identify recalculated
scores from preserved observations; recalculation is not a new model run.

Within-budget travel spending earns the same budget point even when two valid
plans cost different amounts; travel dollars remain visible separately. Mode
preference considers feasible opportunities when the active booking was chosen
or at handoff. Waiting until alternatives expire does not erase an opportunity
that could have satisfied the preference.

No points require a particular agent count, fare label, memory class or forecast
prediction. Strong single-agent and legitimate symbolic policies are allowed.
The score measures observed outcomes and cost, not understanding or authorship.
Two repeats are a small consistency check; the authored hidden bank is not a
statistically independent sample. Hidden cases vary wording, amounts and
combinations within the published contract and introduce no hidden criterion.

## 8. Package and submit

```bash
python submit.py --output submissions/team_solution.zip
```

The ZIP contains only:

```text
solution/config.py
solution/prompts.py
solution/policy.py
SUBMISSION_MANIFEST.json
```

The manifest is automatic. Submit that ZIP by **December 21, 2026 (KST)**
through the announced channel. The exact deadline time will be announced separately. No
notebook, key, framework, generated run, separate report or AI-use disclosure is
required. AI coders may help with implementation, prompts, experiments and analysis.

Final grading reruns your three frozen solution files on all
**96 public-plus-hidden episodes**. Saved local scores do not replace that
evaluation. No best repeat or best bank is selected.

## 9. Leaderboard and help

Staff will publish interim results in a shared Google spreadsheet so teams can
see their own and other teams' scores. The leaderboard will be created later,
and its link will be added here. It will include total /100, each weighted
criterion (including the four request subcriteria), Basic /30, Reactive /30,
Forecast /30, shared API efficiency /10, complete success, grading cost and the
separate API cost estimate. Detailed difficulty outcomes /90 remain available
in the report.

**Final project submission is due December 21, 2026 (KST).** The exact deadline
time and submission channel will be announced separately. The following limits
apply to interim leaderboard grading requests, using Korean calendar dates
(Asia/Seoul):

| Dates in 2026 | Allowed requests per team |
|---|---|
| Through December 13 | One per calendar day. |
| December 14–19, inclusive | No daily limit. |
| From December 20 | Leaderboard grading requests are closed. |

Closing interim feedback on December 20 does not move the final submission
deadline: submit the source ZIP by December 21. The spreadsheet link will be added
here after the leaderboard is created. Final grades use the frozen submission's
task results and grading cost, not leaderboard rank or the best past leaderboard
score.

| Symptom | Next step |
|---|---|
| `No module named framework` in your own interactive session | Run from `project/`, or use the supplied `run.py` rather than executing solution files directly. |
| Key placeholder/authentication error | Edit `project/.env`; check whether an environment variable overrides it. Never send the key in a report. |
| Output directory already exists | Choose another name such as `runs/dev_02`. |
| Protected-file review message | Restore the shared file from the distributed release; put your design in the three allowed solution files. |
| Correct JSON but low score | Inspect current constraints and final state; schema validity does not imply a correct booking. |
| Initial service/handoff failure | Inspect virtual tool time, deadlines, offer windows and confirmation status. |

