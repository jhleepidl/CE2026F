# Student guide

Use this guide as a reference for the scaffold, tools and score. Start with the
[repository README](../README.md) for setup and the submission checklist.

## 1. Set up and run

Follow the [repository setup](../README.md#start-here), using your own distributed
course key. Run commands from `project/`. Begin with `python run.py --offline`,
then inspect a Dev case before making a small paid run. The report records what
the solver saw, did and spent. Use a fresh output path for every experiment.

## 2. Your files and the provided scaffold

| File | What you may change |
|---|---|
| `solution/config.py` | Model/settings, architecture, refresh, routing and policy budgets. |
| `solution/prompts.py` | `PROJECT_PROMPT` and `ROLE_PROMPTS`. |
| `solution/policy.py` | `route()`, `solve()` and helpers inside this file. |

Only these three Python files enter the submitted solver. Framework, evaluator,
accounting, datasets, runners, packagers and release manifest stay unchanged.
Source checks identify review/rerun candidates; they do not establish authorship.
Use the Python standard library, public framework and `requirements.txt` packages.
Extra modules/assets are not copied or installed from a submission.

Separately, create your team's five JSON cases under `local_cases/` using the
[case guide](CASE_GUIDE.md). Submit them in their own ZIP with your solver.

The provided hybrid loop handles source discovery, timed reads, offer search,
local arithmetic, holds, bookings, status checks and monitoring. For operational
cases it interprets conditional terms instead of assuming one budget number.
`REFRESH_CONTEXT=False` deliberately retains the first interpretation. Set it to
`True` to test updates; this is a first experiment, not a guarantee of success.

| Memory or responsibility | Provided | You can improve |
|---|---|---|
| World state | Bookings, holds, spending, current notices and source catalog. | Read it through `world`; do not access the underlying case or future events. |
| Episode memory | Observed offers, read documents and source versions. | Which facts to retain, re-read or pass to each role. |
| Interpretation | Structured conditional terms and current ordinary facts. | Prompts, routing, conflict handling and validation. |
| Purchased terms | Saved refund interpretation and the source version read at purchase. | Preserve the evidence when later versions replace it. |
| Planning | Numerical candidate checks and a simple forecast preparation policy. | Better timing, recovery choices and cost-aware preparation. |
| Verification | Status and final-state checks in the supplied loop. | Recovery from incomplete tool replies and better monitoring. |

Memory lasts for **one trip only**. Each case execution, including a repeat,
starts in a fresh process in both local and official evaluation. Keep the trip's
facts, source versions, bookings and action history in your episode memory.
You may reuse an interpretation within that trip while its source and relevant
prompt/settings remain unchanged. Re-read or reinterpret it when those change.

Do not carry memory or saved interpretations into another case or run, load
answers by case ID, or use case-definition files, future schedules or evaluator
truth to guide the solver. Every model call used to create or refresh memory
must use the supplied API and counts toward that case's cost. The returned
`working_memory`, `context` and `traces` are saved for inspection.

You may replace the loop and memory design in `policy.py`; a custom class is
optional. Case authors can inspect definition files while designing tests;
a running solver uses only its observed inputs.

`hybrid_single` uses one combined interpreter. `hybrid_multi` can send different
observed source groups to traveler, transport and hotel roles, then share their
outputs with the numerical planner. Basic uses a combined interpretation.
`PROJECT_PROMPT` applies to interpretation requests; role prompts affect the
scoped path when routing selects it. Look at saved API instructions to see which
prompt ran. Concurrent API requests change wall-clock waiting, not virtual trip
time or the three shared tool slots. No score requires a particular agent count.

## 3. Understand the trip

The lead traveler's outbound was cancelled. Arrange a replacement that meets the
current meeting, access and carrier requirements. Preserve the existing hotel
and colleague's return. Remove the pending USD 55 hotel fee with the applicable
evidence, and use only the traveler-approved spending authority.

Read the actual current sources. An instruction for a colleague or a later trip
does not automatically apply here. An amendment can replace one condition while
leaving others active. Exact approval and evidence strings come from observed
sources; do not assume their prefixes or lengths.

| Level | Main decision |
|---|---|
| Basic | Interpret a stable request and contract, choose a suitable trip and verify it. |
| Reactive | Meet the first-booking deadline, then repair the trip after observed changes. |
| Forecast | Plan before an uncertain change, including fare terms and closing recovery windows. |

Cases run for at most 36 virtual minutes with three tool slots. The supplied
operational examples require first booking by minute 12. Their Basic handoff
starts at minute 12; advanced examples monitor through minute 28. Basic has no
later external updates. Read the case's actual cutoffs;
a hotel deadline or sale window can close earlier. A forecast is a possibility,
not an observed delay. Search and booking arrivals already include realized
delays; do not add them again.

Some spending permissions depend on the chosen carrier, mode, arrival, price
comparison or a live reservation. The engine checks the **total spending ceiling
at the completion of a paid hold or confirmation**. Total spending includes
retained charges and the pending hotel fee. An old purchase that was approved at
the time remains approved after a later limit reduction. Current arrival, access
and carrier requirements still matter at handoff.

Search displays the base fare (`locked`, `fee` or `flexible`), any reservation
deposit and a link to relevant terms. Read conditional riders before relying on
a refund. A rider's terms freeze when the ticket is confirmed; the condition is
evaluated against the real facts when cancellation completes. A later source
version does not rewrite a purchased ticket's terms.

A paid hold charges its visible deposit immediately. Confirmation credits that
deposit **once** toward the quoted fare; an unused deposit remains spending.
Holding every option can therefore waste the budget. There is no arbitrary
hold-count limit. Cancel the current replacement before confirming another, and
use `status` after an uncertain confirmation reply. A valid hold protects quoted
inventory only until its own expiry.

A source must already be in the current catalog before submitting a `read` batch.
For example, complete `hotel-terms` before requesting its linked bulletin in a
later batch. Failed reads still consume time.

## 4. Use the supplied tools and API

Your `solve(world, api, config, route_fn)` receives two controlled interfaces:

| Interface | Purpose |
|---|---|
| `world.observe()` | Current time, notices, source catalog/versions, bookings, holds and spending; no time advance. |
| `world.call(tool, **arguments)` | Run one local tool. |
| `world.batch(actions)` | Run independent tools using three common slots. |
| `api.json(config["model_settings"], instructions, payload, schema, label)` | Make a schema-constrained model request and record its usage/cost. |
| `api.decide(payload, questions, label, *, task=None, model="gpt-6-luna")` | Ask named choice/predicate/score questions and record their usage/cost. |
| `api.usage()` | Read this episode's usage across both endpoints. |

All model requests must use `api.json` for Responses or `api.decide` for
Decisions. They share the existing spending/call guards and ledger. Do not create
a separate client, bypass accounting or automatically retry/switch endpoints after
an API error. Responses through `api.json` supports these settings:

| Model | `EFFORT` values | `VERBOSITY` | Sampling controls |
|---|---|---|---|
| `gpt-6-luna` | `none`, `low`, `medium`, `high`, `xhigh`, `max` | `low`, `medium`, `high`, or `None` | Only with `EFFORT="none"`. |
| `gpt-5.6-luna` | `none`, `low`, `medium`, `high`, `xhigh`, `max` | `low`, `medium`, `high`, or `None` | Only with `EFFORT="none"`. |
| `gpt-5.4-nano` | `none`, `low`, `medium`, `high`, `xhigh` | `low`, `medium`, `high`, or `None` | Only with `EFFORT="none"`. |
| `gpt-5-mini` | `minimal`, `low`, `medium`, `high` | `low`, `medium`, `high`, or `None` | Keep both `None`. |
| `gpt-5-nano` | `minimal`, `low`, `medium`, `high` | `low`, `medium`, `high`, or `None` | Keep both `None`. |
| `gpt-4o-mini` | `None` | `None` | Supported. |

### GPT-5 Mini and Nano API shutdown — November 11, 2026

`gpt-5-mini` and `gpt-5-nano` will shut down on **December 11, 2026**,
before the project's **December 21, 2026** final source deadline.
If your solution uses either model, select another supported course model in
`solution/config.py` and rerun Dev evaluation before December 11.
Check both answer quality and API cost after changing the model.

See the [official OpenAI API notice](https://developers.openai.com/api/docs/deprecations).

To try `gpt-6-luna` through Responses, set `MODEL="gpt-6-luna"` in
`solution/config.py`; choose its supported controls from this table.

The Responses classroom output cap is 16–4096 tokens. Use `None` for optional verbosity or
sampling controls where the table permits it; choose a listed `EFFORT` value.
The effort string `"none"` and Python `None` are different values. Where
sampling is supported, set `TEMPERATURE` (0–2) or `TOP_P` (0–1), not both.
Unsupported combinations fail locally before a paid request. See
[`framework/settings.py`](framework/settings.py) for the exact adapter and
accounting prices. Compare measured task outcomes and cost when changing models.

### Use Decisions for a typed decision

`api.decide` accepts observed text or a JSON-serializable payload and a list of
named questions. It returns a dictionary containing the raw typed `answers` and
usage. Only `gpt-6-luna` is supported on this endpoint. Do not pass Responses
controls such as effort, verbosity, temperature or an output-token cap.
Use a model-enabled `ARCHITECTURE`, such as `hybrid_single`, when making model
requests. The `rules` setting selects a zero-API run and passes `api=None`.

| Question type | Definition | Main answer field |
|---|---|---|
| `choice` | Supply distinct `choices` with `value` and `description`. | `choice`: one supplied value, plus probabilities/confidence. |
| `predicate` | Ask whether an observed condition holds. | `probability`: the model's estimate from 0 to 1. |
| `score` | Supply ordered `levels` with `label` and `description`. | `score`: a probability-weighted level index, which may be fractional. |

For example, inside a custom `solve()` after reading evidence, ask about current
observed offers. Here `trip_state` contains your interpreted current requirements
and `offers` comes from an actual search:

```python
if len(offers) >= 2:
    decision = api.decide(
        payload={"observation": world.observe(),
                 "trip_state": trip_state, "offers": offers},
        questions=[{
            "name": "offer_id", "type": "choice",
            "instructions": "Propose an observed offer for the current trip. "
                            "Consider the supplied requirements and fare terms.",
            "choices": [{"value": offer["id"], "description": str(offer)}
                        for offer in offers],
        }],
        label={"role": "offer_selector"},
    )
    answer = next(row for row in decision["answers"]
                  if row.get("name") == "offer_id")
    if answer.get("type") == "choice":
        proposed_id = answer["choice"]
```

This proposes an ID, not a booking. Check the proposal against the current
requirements, then use normal tools and verify their results. Read the selected
`choice` value rather than treating a probability as an ID. Probabilities and
confidence are model estimates, not proof of eligibility, authorization or a
successful booking. The optional `task` tag labels the local request record; it
does not store conversation memory or guarantee prompt-cache reuse.

`solution/policy.py` also provides
`choose_offer_with_decisions(observation, trip_state, offers, api)` as an optional
example for a custom loop. The default starter does not call it. Compare a
Decisions-based policy with a Responses policy on the same cases and observed
inputs; a different endpoint, model or context design can change the result.
For the underlying answer types, see the
[official OpenAI Decisions documentation](https://developers.openai.com/api/docs/guides/decisions).

Current project accounting for `gpt-6-luna` Responses uses USD 0.10 per million
regular input tokens, USD 0.01 cached input, USD 0.125 cache writes when reported,
and USD 0.50 output. A cache-write rate replaces the regular-input rate for those
tokens; it is not an added fee on top of that rate. Decisions uses USD 0.10 per
million input tokens, including cached input, with no separate output or cache
fee. These are the published accounting rates; compare complete-task outcomes
and both cost views rather than assuming the new model or endpoint must win.

### Travel tools

| Tool | Virtual duration | Main arguments and result |
|---|---:|---|
| `search` | 2 | Current offers with IDs, prices, arrivals and fare terms. |
| `read` | 2 | `id`: source ID already in the catalog before this batch is submitted; returns its text and version. |
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
`travel_action(...)`. Read `hotel-terms`, wait for that read to complete, and
request its linked bulletin in a later batch. Every `read` source must appear in
`world.observe()["source_catalog"]` before the batch is submitted. Knowing an ID
does not satisfy this prerequisite. A terms read and its bulletin read in the
same batch are not sufficient; a rejected read still takes two virtual minutes.
Inspect the current `transport-guide`, `traveler-profile`, and applicable
`weather-forecast`.

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

## 5. Inspect the data

Nine Dev cases illustrate the three difficulty levels. Thirty fixed Public cases
provide larger development examples. Use:

```bash
python inspect_case.py --split dev --case 1
python inspect_case.py --split public --case 1
python inspect_case.py --split dev --case 1 --export-case local_cases/example.json
```

Inspection makes no model calls. [BENCHMARK.md](BENCHMARK.md) explains the supported
variation. Public definition files contain authoring programs and future events;
these are for test development and evaluation, never solver inputs.

## 6. Improve with visible experiments

```bash
python run.py --split dev --limit 2 --output runs/dev_small
python run.py --split dev --output runs/dev_01
python run.py --local-cases local_cases/example.json --output runs/local_01
python run.py --split public --output runs/public_01
```

Open each `report.html`. Start with criterion and difficulty scores, then inspect
a failing episode's tool history, saved memory, model inputs and actual replies.
Check whether the right source version reached the role that needed it. Compare
one change at a time: refresh, source selection, prompt, model, planning or timing.
Keep some self-authored examples aside during development. Public cases can be
overfit; a good exposed-bank score is not proof of broad generalization.

Dev, local and filtered runs report outcome /90, success, token use and both cost
measures. Only a complete unfiltered Public run receives the local /100 score.
That score is not the official leaderboard result. Every official evaluation covers 30 fixed Public, 30 team-contributed and
60 independent Hidden cases, once each. All teams use the same evaluation set.

Runs save source/configuration snapshots, actual requests/replies, actions and
costs. Saved outputs are evidence, not files to edit or required source submissions.
A new paid run makes new requests. Resolve an API setup, timeout, connection,
authentication, rate-limit or spending interruption before starting a fresh run.
Unknown usage blocks a complete score; no automatic paid retry or endpoint
fallback follows an infrastructure error. A bounded repair of a model's content
mistake is allowed, with every request counted.

## 7. Understand the 100-point score

| Criterion | Points | What is checked |
|---|---:|---|
| Usable arrival | 40 | One confirmed, eligible outbound reaches the current required meeting, including transfers. |
| Current requests | 20 | Five each: approved spending, feasible preferred mode, access and permitted carrier. |
| Hotel waiver | 10 | Applicable evidence/version accepted before cutoff, with the room preserved. |
| Safety | 10 | Authorized actions, protected bookings preserved, no duplicate outbound. |
| Reliable handoff | 10 | Timely first booking, verified result, monitoring and complete handoff. |
| API efficiency | 10 | Shared uncached-rate cost allowance compared with all model usage. |

Average the first five criteria across all episodes to get `O /90`. With positive
solver grading cost `S` and the fixed allowance `B`:

```text
score = min(100, O + 10 * min(1, B / S))
```

A valid zero-API solver earns all ten efficiency points. Every model call counts,
including specialist and repair calls. Local numerical computation is free.
For an official grade, `S` includes the recorded model cost of every evaluated
case. Earlier Dev, local Public and case-authoring experiments are separate and
are not added to `S`. Calls that initialize or refresh memory during an evaluated
case still count. There is no student-supplied API-cost baseline for a case package.
Responses grading cost is `(all input tokens * uncached input price + output
tokens * output price) / 1,000,000`. Decisions grading cost is
`all input tokens * 0.10 / 1,000,000`, with no separate output fee. The ordinary
input rate includes cached input for grading. The separate API estimate retains
applicable cache discounts; it is an estimate, not an invoice.

| Evaluation | Episodes | Fixed grading allowance B |
|---|---:|---:|
| Local Public development: 30 cases twice | 60 | USD 0.02407475 |
| Official: 30 Public + 30 team-contributed + 60 Hidden cases once | 120 | USD 0.04814950 |

Both allowances use the same cost reference per episode. They are fixed grading
references, not spending limits.
For example, `O=80` and `S=2B` earn 85/100; cost at or below B earns all ten
efficiency points. Changing case content does not automatically change B.

The official set stays at 120 cases. Each team's accepted five cases replace its
assigned contribution slots; they do not add cases to the total or replace the
fixed Public examples. Team contributions and independent Hidden cases are
managed separately. All cases receive equal outcome weight.

All levels have equal outcome weight:

```text
Basic /30    = mean Basic outcome /90 divided by 3
Reactive /30 = mean Reactive outcome /90 divided by 3
Forecast /30 = mean Forecast outcome /90 divided by 3
Total /100   = Basic + Reactive + Forecast + API efficiency /10
```

Criterion and difficulty columns are two views of the same score, not extra
points. Access/carrier violations can lose both usable-arrival and the relevant
request credit. Within-budget fares receive the same spending credit. A final
suitable booking does not erase an unsafe action or missed first-booking deadline.
Waiting for alternatives to expire does not erase a feasible mode opportunity.
Scores display two decimals but are stored without that rounding.

The scoring version is `travel-score-2026f-v3-100`. Evaluation uses case state,
actions and recorded API cost; an LLM does not grade your answer. No points
require a particular agent count, model, fare label or memory class.

## 8. Package and submit

Email **two ZIPs** to the existing course submission address at every leaderboard
or final submission:

1. Run `python submit.py --output submissions/team_solution.zip`. This contains
   `solution/config.py`, `solution/prompts.py`, `solution/policy.py` and the
   generated source manifest.
2. Build your five-case ZIP using [CASE_GUIDE.md](CASE_GUIDE.md). Include it even
   if the cases are unchanged. This contains data, replay witnesses and a manifest,
   not additional solver code.

Cases are submitted continuously through **December 7, 2026 (KST), inclusive**.
From December 8, attach the same accepted case content with new solver versions.
Witness traces may be regenerated without changing that case content. The final
solver is due **December 21**, with the exact time announced separately.
No notebook, API key, separate report or AI-use disclosure is required. AI coders
may help with all implementation, experiments, prompts and analysis.

## 9. Leaderboard and presentations

Official evaluation includes 30 fixed Public cases, 30 team-contributed cases
and 60 independent Hidden cases. Each team knows its own five contributions;
the other teams' contributions and the independent Hidden cases are not released.
Unreleased cases stay within the [published benchmark scope](BENCHMARK.md).
The case-content cutoff is December 7. A later common selection may change
examples within that scope, without introducing new capabilities.

Every leaderboard comparison accounts for all cases and their API costs on the
same evaluation set. Local runs always start fresh and are for development only.

The spreadsheet link will be added later. It displays total, criterion scores,
Basic /30, Reactive /30, Forecast /30, API efficiency, success and costs.
Until December 13, each team may request grading once per Korean calendar day.
December 14–19 has no daily limit; interim grading closes from December 20.
The final source deadline remains December 21. Final grades use the final frozen
source, not leaderboard rank or a team's highest previous score.

**All final presentations are online via Zoom.** The course presentation schedule
is separate from the source deadline. Joining details will be announced later.
