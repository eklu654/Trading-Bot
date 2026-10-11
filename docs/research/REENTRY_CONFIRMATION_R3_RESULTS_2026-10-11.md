# Re-entry Confirmation R3 Results and Decision — 2026-10-11

## Run status
- Workflow: [run #30](https://github.com/eklu654/Trading-Bot/actions/runs/38119589304) — **success**.
- Branch: `research/qqq-slow-bear-audit`.
- Tested commit: `7ea1ac24e235396803a27702842678a46e989f67`.
- Unit tests passed, backtest completed, and artifact uploaded.
- Artifact: `reentry-isolation-results` (ID `11693869105`).
- Evaluation: 4,189 aligned sessions, 2010-02-11 through 2026-10-07; actual TQQQ, QQQ adjusted-close signals; $5,000 initial capital.
- R3 was added as one fixed, preregistered rule: 50% after +5% from the post-shock low and close above QQQ's 20-session SMA; full exposure after +10% and still above the SMA. Once staged, retain 50% through renewed shocks and reset the recovery low.

## Results

| Candidate | Final at 0 bps | Max DD | Worst rolling 252-session return | Final at 10 bps | Max DD at 10 bps |
|---|---:|---:|---:|---:|---:|
| B0 | $4,040,315 | -73.53% | -72.64% | $3,964,236 | -73.64% |
| R1 immediate | $3,661,412 | -81.15% | -80.52% | $3,535,417 | -81.30% |
| R2 staged/reset | $3,039,512 | -77.14% | -76.37% | $2,964,440 | -77.27% |
| R2P staged/retain | $3,197,012 | -73.44% | -72.54% | $3,136,819 | -73.54% |
| R3 SMA-confirmed staged | $3,752,188 | -73.93% | -73.05% | $3,681,542 | -74.03% |

R3 finishes **7.13% below B0** at zero cost and has slightly worse max drawdown (0.39 percentage points worse) and worst 252-session return (0.41 points worse). At 10 bps it remains about 7.13% below B0, with slightly worse drawdown and worst-year return. The ranking is not rescued at 25 or 50 bps. R3 therefore fails the preregistered decision rule: it does not preserve enough wealth *and* improve downside metrics. **Reject R3; do not tune the SMA length or rebound thresholds.**

R2P is also not a viable improvement: its max drawdown is effectively unchanged from B0, while final wealth is 20.9% lower. R1/R2 are materially worse. Keep B0 as the research control, not as an approved live strategy.

## Event-level diagnostic (zero-cost equity, same frozen inputs)
Nine B0 defensive episodes were identified from the tested QQQ series. The table reports each episode's shock date, B0's 10%-recovery date, and the strategy equity return over that episode window from the prior close through the B0 recovery close. These are overlapping-path attribution windows, not standalone trade returns.

| Shock date | B0 recovery date | Sessions | B0 return | R2P return | R3 return |
|---|---|---:|---:|---:|---:|
| 2011-08-04 | 2011-08-31 | 20 | -10.75% | -7.92% | -9.08% |
| 2018-10-24 | 2019-01-07 | 50 | -9.77% | -21.13% | -23.19% |
| 2020-02-27 | 2020-03-26 | 21 | -23.26% | -39.21% | -23.26% |
| 2020-06-11 | 2020-07-06 | 17 | -9.29% | -3.97% | -3.97% |
| 2020-09-03 | 2020-10-12 | 27 | -16.70% | -11.29% | -11.29% |
| 2022-05-05 | 2022-07-19 | 51 | -16.73% | -21.85% | -21.85% |
| 2022-09-13 | 2022-11-11 | 44 | -15.52% | -11.93% | -10.65% |
| 2025-04-03 | 2025-04-09 | 5 | -23.26% | -23.26% | -23.26% |
| 2026-06-05 | 2026-08-13 | 48 | -9.81% | -12.65% | -12.65% |

Interpretation: R3 did not consistently improve the loss path. It matched B0 in the initial COVID crash window, helped relative to B0 in some smaller/rebound windows, but lagged in other prolonged windows; its aggregate terminal wealth and downside metrics confirm there is no robust net benefit. The short 2025 episode is only five sessions and is not evidence of a durable detector. This data covers actual TQQQ history only; it says nothing directly about the 2000 bear market.

## Decision and next step
1. Keep B0 unchanged as control; reject R1/R2/R2P/R3 as replacement candidates based on this bounded test.
2. Stop re-entry threshold tuning. The next research task should be a separate, bounded **prolonged-stress detector** hypothesis, with explicit fast-recovery guardrails and a preregistered stop rule. It must be tested on multiple episodes and should not be tailored solely to 2000.
3. Any pre-2010 Nasdaq/TQQQ-like stress test must use clearly labeled synthetic daily-reset returns on the underlying index; never present it as actual TQQQ history.
4. No candidate is approved for paper/live trading by this experiment.

## Artifact hashes
- QQQ frozen input SHA-256: `c2d431aa9582c9f20e2337d6761ef67173cf741f1eeb006114b99d5e8b49ae32`
- TQQQ frozen input SHA-256: `660110f7544cd7846452283194d043211d62ea3c03ae2c4069701ce20e11728c`
- Summary SHA-256: `2dbeab019c53c18c8431435581ba11e08414073d1e5991d18844883de13fa8b1`
- Equity curves SHA-256: `585e4fcbe1e5b69ad3b126005aee7150a5923aeb1bc89137b1070bc87fac3759`
