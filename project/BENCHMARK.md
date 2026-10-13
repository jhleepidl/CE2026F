# Benchmark guide: what to build and how to test it

Build an assistant that keeps a usable trip after new information arrives. It
must read the current request and sources, choose approved actions, and check
what the booking tools actually did. You may combine model calls with ordinary
Python planning. Agent count, writing style and agreement with a weather forecast
are not scoring criteria.

## Supplied cases and final evaluation

| Set | Distinct cases | Use |
|---|---:|---|
| Dev | 9: three per difficulty | Start, debug and compare small changes. |
| Public | 24: eight per difficulty | Two runs per case; provisional public grade. |
| Hidden evaluation | 24: eight per difficulty | Two runs per case, combined with Public for final grading. |

Final grading uses all 96 episodes from one frozen submitted solution. Each
team gets the same cases and tools in separate worlds. Local test cases you
create are optional and do not enter the official grade.

The tables below explain the published behaviors. They are a coverage guide,
not a promise about exact hidden wording, amounts or situation frequencies.
Hidden cases use this same contract and add no secret scoring criterion. Public
cases can be overfit; no finite authored bank establishes performance on arbitrary
real travel. The [100-point rubric](README.md#7-understand-the-100-point-score)
uses 90 outcome points plus up to 10 API-efficiency points under
`travel-score-2026f-v3-100`. Grading cost counts every input token, including
cached input, at the model's uncached-input rate, plus output at its output rate.
The report separately shows the usage-based API cost estimate with cache
discounts. The grading measure is not an actual invoice.

## Two clocks and scheduled changes

A meeting time such as 11:30 is a clock time: 690 minutes after midnight. The
simulator also has a virtual clock starting at minute 0. Tools advance that
clock; model calls and Python computation do not. For example, a terminal
arrival of 09:10 plus a 35-minute transfer means arrival at the client at 09:45.
It does not mean virtual minute 585 has passed.

`observe()` shows current public state without advancing time. Search and reads
usually take two virtual minutes; a hold takes one and a confirmation takes two.
Up to three independent tools can run together for every policy. Read the
[tool table](README.md#4-use-the-supplied-tools-and-api) before scheduling actions.

External updates happen at fixed virtual times in each case. They may change a
request, source, price opportunity, inventory or observed arrival. These are
fictional scheduled events, not live weather, real provider APIs or a new random
world for each team. Reading a source again before its update returns the same
version. Reading after the update can return different information. Events at a
tool's completion time apply before that tool completes.

Model replies can still vary. The two official repeats are a small consistency
check; they do not turn the authored cases into a large independent sample.

## Basic: make and verify a suitable trip

Basic has no later external updates. Choose a replacement that meets the current
meeting time, approved spending, feasible mode preference, access requirements
and carrier rules. Claim the hotel fee waiver without cancelling the room, keep
the colleague's return, and verify the replacement. You may finish immediately
when the trip is complete. The horizon is virtual minute 36.

## Reactive: keep a valid trip when facts change

Confirm a first outbound by virtual minute 14, then keep responding through
minute 24. You may repair it later with approval and must finish by minute 36.
Waiting for all future messages before making a first booking misses the early
service obligation.

| Situation | What can change | What your assistant should handle |
|---|---|---|
| Meeting update | The client meeting moves; hotel check-in or lunch may have another time. | Use the latest applicable client deadline, including the onward transfer. |
| Budget update | The limit for new spending falls. | Apply the new limit to new commitments; earlier approved purchases remain approved. |
| Temporary preference | The traveler prefers a different mode for this trip. | Keep current-trip instructions separate from defaults for later journeys. |
| Conditional waiver | The hotel publishes a new evidence procedure or source version. | Use the current evidence type, literal code and version before the cutoff. An already accepted claim remains accepted. |
| Quote expiry | Another buyer takes unheld inventory or an offer closes. | Search current offers and respect hold expiry; an old quote alone cannot reserve a seat. |
| Confirmation interruption | The provider commits a booking but its reply is lost. | Check the same request key before starting another booking. |
| Transfer update | The journey from the terminal to the client changes. | Refresh the guide; terminal arrival and client arrival are different. |
| Traveler scope | Access or carrier rules change for the lead traveler. | Apply them to the current replacement, including one already booked; preserve the colleague's separate booking. |

Cases can combine later restrictions with an earlier situation. A new notice may
remove an old restriction as well as add one. Keep unrelated conditions when a
single field changes. Do not infer the latest rule from a case ID or family name.

## Forecast: commit before the future is known

Forecast adds uncertain weather, different fare contracts and limited recovery
windows. Confirm a first outbound by virtual minute 12, keep responding through
minute 24 and finish by minute 36. Read the applicable forecast before choosing
a fare. A higher price may buy useful flexibility, but the most expensive fare
is not automatically suitable.

The published public cases cover four integrated situations, each with a delay
and a false-alarm outcome:

| Situation | Combined changes |
|---|---|
| Flight watch and access | The flight warning rises, followed by an earlier meeting, step-free access and a current carrier rule. |
| Rail watch and carrier | The rail warning falls, while the meeting, access and permitted carrier also change. |
| Coach watch and transfer | The coach warning rises; later meeting/carrier rules and onward transfers can change. |
| Changed watch and trip scope | The warning shifts from rail to flight, followed by current-trip preference, access, carrier and spending changes. |

A forecast percentage is a warning about a stated journey and mode. It is not
an already observed delay, and the authored outcomes are not random draws from
that percentage. The cases are not a weather-calibration study. The realized
report can confirm a delay or a false alarm. Current search and booking arrivals
already include an observed physical delay; do not add it twice. A sensible hedge
can pass without predicting exactly which forecast will come true.

## Sources, booking terms and failures

Use current, applicable evidence. A source may contain a withdrawn procedure,
another guest's example or a rule for another traveler. Source IDs tell you which
document you read; they are not necessarily the evidence category needed by a
claim. Preserve literal approval and evidence codes without dropping characters.
When a source version changes, check which remembered facts need another read.

Search results include arrival times, mode, carrier, access, price, opening and
closing times, current availability and fare terms:

- `locked`: cannot be cancelled after confirmation.
- `fee`: approved cancellation refunds the fare minus `cancel_fee_usd`.
- `flexible`: approved cancellation refunds the whole fare.

Cancel the existing replacement before confirming another. Retained cancellation
fees remain part of spending. Outbound approval never authorizes changing the
hotel or colleague's return. A cheaper ticket that cannot be repaired may become
unusable; a flexible ticket can also be too expensive or fail access/carrier rules.

Waiver claims must complete strictly **before** the stated cutoff. Offers close
at their expiry, and a hold becomes invalid at its expiry. Test boundary times,
including the duration of the action, rather than assuming that starting before
a deadline is enough.

A simulated lost confirmation reply leaves the outcome unknown until checked.
Use `status` with the original request key. Reusing that same key and payload is
idempotent: it does not make another booking. A new key can duplicate the trip.
Spending is checked when a confirmation completes using the current limit,
retained transport spending and any pending hotel fee. A later budget reduction
does not undo an earlier approved purchase, while new meeting/access/carrier
rules still apply to the trip at handoff.
An actual model API timeout is different: the evaluator stops, preserves partial
records and unknown costs, and does not automatically retry.

## Make your own local tests

You may create JSON test files in `local_cases/` without changing the protected
framework or official data. These files are ignored by Git, not submitted and
not officially graded. Your submitted implementation remains the same three
files under `solution/`.

Run from `project/` to copy one existing dev case into a JSON list:

```bash
python inspect_case.py --split dev --case 1 --export-case local_cases/example.json
```

Start with a meaning-preserving wording change. This Python example changes only
the case's display ID and one phrase; it does not invent new trip facts:

```python
import json
from pathlib import Path

cases = json.loads(Path("local_cases/example.json").read_text())
cases[0]["case_id"] = "my-wording-check"
cases[0]["initial_request"] = cases[0]["initial_request"].replace(
    "Plan my replacement outbound", "Please arrange a replacement outbound", 1
)
Path("local_cases/my_cases.json").write_text(json.dumps(cases, indent=2) + "\n")
```

Inspect your case without a model call, then run your current solution on it:

```bash
python inspect_case.py --local-cases local_cases/my_cases.json --case 1
python run.py --local-cases local_cases/my_cases.json --output runs/local_01
```

A local run uses one repeat and reports outcomes /90, criterion failures,
difficulty results, full success, grading cost and estimated API cost. It has no official /100
grade and does not borrow the full Public bank's cost allowance.

The exported definition includes structured simulator fields and future events
for local authoring. Keep these out of model inputs and solver decisions. The
solver uses only observations and tool replies that have actually arrived.

If you change a **fact**, update every matching representation. For example:

| Change | Keep consistent |
|---|---|
| Meeting or budget | Initial request, `deadline`/`budget`, applicable source prose and later event `changes`. |
| Carrier, access or preferred mode | Request/profile scope, structured rules, offer fields and later notices. |
| Approval or waiver evidence | Literal codes, evidence type, version, current bulletin and any revised procedure. |
| Offer ID or travel terms | `options`, every event referencing that ID, fare fees, offer windows and any prose quoting the offer. |
| Weather or transfer | Current source text, corresponding structured transfer/event changes and resolved-weather text. |

Changing prose alone does not change what the simulator checks. A file that
loads successfully can still contain contradictory text or an impossible trip.
Check the expected behavior and whether a valid action sequence is possible
before interpreting a failure as a model problem. A model's opinion that a trip
looks correct is not a substitute for booking and outcome checks.

## Useful tests to design

Choose a few tests for a specific weakness instead of generating many near copies.
Keep the solution files and settings fixed when comparing two versions of a case.

- Reword one request while preserving its facts and literal codes.
- Rename carriers or reorder offers without changing eligibility; do not make an
  identifier itself the answer.
- Move a source revision near a read or claim completion; check the version and
  strict cutoff.
- Test a new restriction and a lifted restriction, plus a colleague-only notice.
- Compare a valid early booking followed by repair with an attempt that waits
  past the first-booking deadline.
- Test a locked fare, an affordable fee-based repair and a flexible fare that
  exceeds the budget or fails another requirement.
- Keep early weather evidence the same in two authored cases, but synchronize the
  later realized report and delay fields for delay/no-delay outcomes.
- Check a lost confirmation reply using status, and inspect that no duplicate
  outbound was created.

Keep some of your local cases aside while developing, then run the same frozen
solution on them. Separate failures by Basic, Reactive and Forecast and compare
both cost estimates as well as outcomes. These tests can expose fragile behavior. Their
results do not guarantee generalization, establish that several agents are best,
or disqualify a correct general parser or local optimizer.
