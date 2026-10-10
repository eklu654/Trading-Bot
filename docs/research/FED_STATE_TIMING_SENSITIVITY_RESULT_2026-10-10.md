# Fed-State Timing Sensitivity — Result — 2026-10-10

## Purpose

Test whether changing only the Fed-state market-calendar lag changes the existing Fed-paused/200-DMA overlay outcome. This is a one-session timing sensitivity, not a direct reimplementation of the two individual announcement/effective-date rows. The Fed classifier, QQQ/TQQQ rows, B0 shock/recovery logic, 200-DMA, sticky overlay exit, next-open execution, and cost model are unchanged.

## Reproducibility

- Workflow: [run 38043580560](https://github.com/eklu654/Trading-Bot/actions/runs/38043580560), success
- Branch: `research/qqq-slow-bear-audit`
- Tested SHA: `f1945b27c9c9eb1809b916850a7a14fb5fef6aba`
- Artifact: [fed-state-timing-sensitivity](https://github.com/eklu654/Trading-Bot/actions/runs/38043580560/artifacts/11666710713)
- Artifact SHA-256: `sha256:e3abdac865120720115c9e770446f5d0b8f1ae3efea67bc849306f5f98096c8e`
- Market-input fingerprint in manifest: `74ba4b9e78f1154538349ae93368e190eb94ef775ea48e4ffba765401f4c7dec`
- Common market rows: 4,189 sessions, 2010-02-11 through 2026-10-07; $5,000 initial balance; nine baseline shock/recovery events.

## Results

### Full-period results

| Variant | Cost | Ending balance | CAGR | Max drawdown | Defensive signal sessions |
|---|---:|---:|---:|---:|---:|
| B0 baseline | 0 bp | $4,040,316 | 49.49% | -73.53% | 274 |
| Same-session Fed-state mapping (diagnostic) | 0 bp | $2,832,649 | 46.33% | -73.53% | 299 |
| Existing one-session-lag Fed-state mapping | 0 bp | $2,908,572 | 46.57% | -73.53% | 298 |
| B0 baseline | 10 bp | $3,964,237 | 49.32% | -73.64% | 274 |
| Same-session Fed-state mapping (diagnostic) | 10 bp | $2,740,652 | 46.04% | -73.64% | 299 |
| Existing one-session-lag Fed-state mapping | 10 bp | $2,819,746 | 46.29% | -73.64% | 298 |
| B0 baseline | 25 bp | $3,852,659 | 49.06% | -73.80% | 274 |
| Same-session Fed-state mapping (diagnostic) | 25 bp | $2,608,066 | 45.61% | -73.80% | 299 |
| Existing one-session-lag Fed-state mapping | 25 bp | $2,691,410 | 45.88% | -73.80% | 298 |

### What changed

- The mapped Fed-state labels differed on 21 sessions, including the initial insufficient-history boundary and state transitions.
- The overlay exposure signal differed on exactly **one** session: **2016-03-15**.
- On that date, same-session mapping classified the prior-rate lifecycle as `TIGHTENING_PAUSED` and entered the overlay, while the one-session-lag version still classified it as `TIGHTENING_ACTIVE` and stayed exposed.
- The candidate signal differed on that same one session only.
- The one-session-lag variant finished about **$75,923 (2.68%)** above the same-session variant at 0 bp, **$79,094** above at 10 bp, and **$83,344** above at 25 bp.
- Both overlay timing variants had the same reported maximum drawdown at each cost setting.

## Interpretation

1. **The lag convention has a measurable but localized impact.** A one-session difference in the state label changes only one actual portfolio signal in this 4,189-session sample, but that single exposure difference compounds into roughly $76k–$83k in ending-balance difference.
2. **The timing tweak does not fix the overlay's overall trade-off.** At zero cost, the existing one-session-lag candidate ends about $1.132M (28.0%) below B0 and does not improve maximum drawdown. The same-session variant ends about $1.208M (29.9%) below B0 with the same maximum drawdown.
3. **No evidence here justifies changing the established lag.** The zero-lag variant is not approved for live use. The conservative one-session lag remains the control convention.
4. **The two December 2015/2016 announcement/effective-date flags did not themselves create an overlay-signal disagreement in this run.** This broad lag sensitivity changes other state boundaries too; it should not be misrepresented as a targeted portfolio counterfactual for just those two hikes.
5. This is a retrospective development sample, not an untouched holdout. No strategy is promoted and paper/live trading is not authorized.

## Next step

Keep the existing one-session Fed lag and B0 unchanged. The more important finding is that the paused-Fed/200-DMA candidate loses substantial terminal wealth without improving maximum drawdown in this run; do not spend more time optimizing its timestamp convention. If Fed timing research continues, make the next experiment a narrowly versioned announcement-versus-effective-date transformation at only the verified 2015 and 2016 rate changes, and first require it to demonstrate an actual state/position difference before running another full strategy backtest.
