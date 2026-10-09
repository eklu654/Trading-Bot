# Historical Real-Index Fed/DMA Defense Study — First Causal Run

**Run date:** 2026-10-09 UTC  
**Status:** Successful exploratory result; historical Fed state is a proxy, not exact modern state-builder replication.  
**Workflow:** [run 37892712141](https://github.com/eklu654/Trading-Bot/actions/runs/37892712141)  
**Artifact:** `historical-real-index-fed-dma-defense`, ID `11599435954`  
**Code commit:** `545213092ddf7ec00977b790ecdd7448daa62eed`

## What was tested

Actual daily Nasdaq Composite (`^IXIC`) and S&P 500 (`^GSPC`) OHLC price-index observations were tested from 1971-02-05 / 1971-01-04 through 2026-10-08, respectively. The data contain 14,036 Nasdaq sessions and 14,060 S&P sessions. Historical rates came from FRED `DFF` (daily effective federal funds rate); cash return used FRED `TB3MS` (monthly 3-month Treasury bill yield), lagged one month.

This is an **unleveraged real-index exposure study**, not a TQQQ reconstruction and not a claim about pre-inception TQQQ portfolio wealth.

### Historical Fed state limitation

The modern candidate's lifecycle state uses the federal-funds target-range series and labels `TIGHTENING_ACTIVE` based on target-rate hikes within a trailing 90-day window. That target-range source does not cover the 1970s. This first long-history run therefore uses a clearly distinct DFF proxy: state is active when the effective federal-funds rate is more than 1 basis point above its value 90 calendar days earlier, after a conservative one-calendar-day data-availability shift and one index-session state lag. This proxy is imperfect and must not be described as an exact reproduction of the modern target-rate state.

The combined defense uses actual index close below its 200-session simple moving average plus the lagged DFF proxy state. Once armed, it remains active until the index closes back at/above its 200-DMA. Close-derived changes execute at the next session's open; the previous exposure applies to the overnight gap and the new exposure applies intraday. Fed-only and DMA-only are ablations. Defensive exposure was set to 0%, 25%, 50%, or 75%; the rest earned either lagged TB3MS cash yield or, for the combined rule, zero cash yield as a sensitivity. All results use price-index returns, excluding dividends.

## Whole-history results

Normalized wealth starts at 1.0; it is not dollars and not TQQQ.

| Index / mechanic | Defensive exposure | Ending wealth | CAGR | Max drawdown | Worst rolling 252-session return |
|---|---:|---:|---:|---:|---:|
| Nasdaq Composite, no defense | 100% | 271.93x | 10.59% | -77.93% | -62.89% |
| Nasdaq Composite, combined | 0% | 779.87x | 12.71% | -51.26% | -41.52% |
| Nasdaq Composite, combined | 25% | 657.40x | 12.36% | -56.34% | -46.49% |
| Nasdaq Composite, combined | 50% | 521.00x | 11.89% | -63.16% | -51.64% |
| Nasdaq Composite, combined | 75% | 388.20x | 11.30% | -71.15% | -56.81% |
| S&P 500, no defense | 100% | 85.19x | 8.30% | -56.78% | -48.82% |
| S&P 500, combined | 0% | 100.69x | 8.62% | -27.07% | -21.89% |
| S&P 500, combined | 25% | 103.56x | 8.68% | -31.20% | -24.97% |
| S&P 500, combined | 50% | 101.51x | 8.64% | -40.33% | -31.79% |
| S&P 500, combined | 75% | 94.78x | 8.51% | -48.76% | -39.33% |

The combined defense spent 3,314 Nasdaq sessions and 3,315 S&P sessions in the defensive state, with 208 and 266 executed exposure transitions, respectively. By comparison, DMA-only defense was active for 4,010 Nasdaq and 3,873 S&P sessions; the Fed-only proxy was active for 6,541 sessions on both series.

## Zero-yield cash sensitivity

With no interest earned on defensive cash:
- Nasdaq combined at 0% exposure in defense ended at **394.42x** versus **271.93x** for no defense; maximum drawdown was **-54.75%** versus **-77.93%**.
- S&P combined at 0% exposure in defense ended at **51.91x** versus **85.19x** for no defense; maximum drawdown improved from **-56.78%** to **-28.64%**.
- S&P combined at 25% defensive exposure ended at **63.01x**, also below no-defense terminal wealth, while reducing maximum drawdown to **-31.60%**.

This makes the cash-yield assumption material, particularly for S&P terminal wealth. The defense is not a free improvement: lower defensive exposure reduces drawdown but can materially reduce compounding when the index recovers or trends upward.

## Selected historical episodes

Returns are price-index returns over the listed calendar windows, with the state mechanic applied causally and cash yield included for the primary results.

| Episode | Nasdaq: combined 0% defense | Nasdaq: no defense | S&P: combined 0% defense | S&P: no defense |
|---|---:|---:|---:|---:|
| 1973–74 bear window | +14.39% | -41.96% | +13.83% | -23.60% |
| 1980–82 inflation window | +90.90% | +53.77% | +42.50% | +30.29% |
| 1987 crash window | -1.25% | -13.87% | -3.99% | -18.76% |
| 2000–02 dot-com bear | -30.37% | -67.18% | -16.33% | -40.12% |
| 2007–09 financial crisis | -14.45% | -32.07% | -19.35% | -39.79% |
| 2022 tightening bear | -9.92% | -33.10% | -8.98% | -19.44% |

These are episode-window returns, not peak-to-trough returns for each crisis. The predefined windows and complete event-level outputs are in the artifact's `episodes.csv` and `transitions.csv`.

## Data manifest

The workflow artifact contains the daily close and open files, `fed_state_daily.csv`, `summary.csv`, `episodes.csv`, `transitions.csv`, and `manifest.json`. The manifest records SHA-256 hashes for each index OHLC series and the DFF/TB3MS inputs.

- Nasdaq close+open combined hash: `23edf7e1cee17b8a18e736a3260502cb985042193afceb19091bc2cd0fed3018`
- S&P close+open combined hash: `50c270d861263aaf4de66c9bba5e8c859689aff15709541f95fc0e3e597d3d46`
- DFF hash: `c4fd6f79de05010b22a23c7913d4902903c104129efeee3e09db72669e72d9b3`
- TB3MS hash: `0f6a8ee7f9b68bf893011b03264750bd00e9f47ce6ac17ab45fd3a669eec9f83`

## Conclusion and next gate

**Preliminary evidence supports the defense as a real-index risk-control mechanic across several historical regimes**, not only 2022: the combined rule improved whole-history maximum drawdown and worst rolling-year returns on both price indexes, and under the Treasury-bill cash assumption also improved terminal wealth in this run. The zero-yield sensitivity shows terminal-wealth conclusions are cash-return-dependent, especially on the S&P 500.

Do not select this as the final TQQQ overlay yet. Next:
1. Improve the long-history Fed state proxy by reconstructing explicit hike/cut events from DFF with a documented material-change threshold and a trailing 90-day lifecycle, then compare sensitivity against the current net-rate-change proxy.
2. On the overlapping post-2008/2010 interval, compare the proxy's state dates with the existing target-rate state builder; document disagreement rather than pretending equivalence.
3. Add a total-return index cross-check if a consistently sourced, sufficiently long series can be obtained.
4. Test turnover/slippage/cash assumptions and episode concentration.
5. Only after those gates, decide whether this supports another actual-TQQQ candidate test on 2010+ data.

## Execution and debugging audit

- Initial workflow [37892097538](https://github.com/eklu654/Trading-Bot/actions/runs/37892097538) failed because Pandas 4 returned incompatible datetime resolutions for the index and FRED merge keys. Source date keys were normalized before the as-of joins.
- Workflow [37892320969](https://github.com/eklu654/Trading-Bot/actions/runs/37892320969) reached the analysis but failed at the final console summary because the displayed transition-column name did not match the newly separated signal/executed-transition metrics. The reporting column was corrected.
- Final workflow [37892712141](https://github.com/eklu654/Trading-Bot/actions/runs/37892712141) passed all steps and uploaded the complete artifact.
- The final code explicitly downloads and archives real index open and close prices. A signal observed at close only changes exposure at the next session's open; prior exposure is applied to the overnight gap and the new exposure intraday. The no-defense control matches the actual index close-to-close path.
