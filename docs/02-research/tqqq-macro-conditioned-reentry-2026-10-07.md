# TQQQ Macro-Conditioned Re-entry Research — 2026-10-07

## Decision

**Reject macro-conditioned re-entry as a replacement for immediate re-entry.**

The hard 100-DMA exit remains mandatory. Macro state may not cancel the initial defense, and the tested macro veto on re-entry materially reduced compounding.

## Canonical synthetic control

- Starting balance: **$5,000**
- Data: QQQ adjusted close/open
- Synthetic daily-reset 3x QQQ
- Signal: close-to-next-open
- Costs: 0%
- Cash yield: 0%
- Period: 1999-03-10 through 2026-10-05

| Strategy | Ending balance | CAGR | Max drawdown | Avg exposure |
|---|---:|---:|---:|---:|
| Immediate 100-DMA baseline | **$128.315B** | **85.69%** | **-45.97%** | 69.10% |
| Macro-confirmed exit-only | $196.039M | 46.77% | -98.13% | 82.38% |
| Macro-conditioned re-entry | **$866.797M** | **54.90%** | **-45.97%** | 56.21% |

The macro-conditioned re-entry test keeps the mandatory 100-DMA exit, then vetoes re-entry while the fixed macro classifier is in one of four dangerous states: acute shock, structural tightening, inflation/liquidity tightening, or economic/credit deterioration.

Break audit: 6 acute-shock, 34 economic/credit, 7 inflation/liquidity, 13 structural-tightening, and 69 normal/mixed DMA breaks. The macro classifier therefore contains information about break severity, but using it to delay re-entry destroys too much compounding value.

## Shock-only follow-up

A focused follow-up tested only a predeclared volatility/shock re-entry veto:

- VIX 20-day increase >= 100%, **or**
- QQQ 20-day realized-volatility increase >= 100%.

Result over the same synthetic framework available to that run (through 2026-10-02):

| Strategy | Ending balance | CAGR | Max drawdown | Avg exposure |
|---|---:|---:|---:|---:|
| Immediate 100-DMA baseline | **$131.344B** | **85.85%** | **-45.97%** | 69.08% |
| Shock-only re-entry veto | $87.932B | 83.16% | **-45.97%** | 68.51% |

The shock-only rule produced **40 re-entry veto events** and still reduced terminal wealth substantially without improving maximum drawdown.

## Three-layer contextual exception: separate finding

The failed macro-conditioned **re-entry** experiments must not be conflated with the separate contextual Fed exception that was tested later.

Frozen contextual rule:

- If QQQ is below the 100-DMA,
- Fed target rate is > 3.5%,
- and QQQ's 60-day return is non-negative,
- temporarily remain invested rather than obeying the DMA exit.

A subsequent predeclared shock override then exits even during that exception when either VIX 20-day change or QQQ 20-day realized-volatility change reaches +100%.

That architecture produced approximately **$204.86B** versus **$128.32B** for the immediate 100-DMA baseline over the full synthetic period, while retaining the baseline's **-45.97%** maximum drawdown. Through the same endpoint, the conditioned layer alone was approximately **$183.10B**, so the shock override added another approximately **$21.76B** of terminal wealth.

The event-attribution audit found **85 contextual-veto/shock-overlap events** (80 veto-only and 5 overlaps). This is important evidence that the result is not literally one or two special days. However, the individual one-day counterfactual impacts are **not additive** because changing one day's exposure changes subsequent compounding. Therefore we should not sum those event impacts and call the sum the strategy's causal contribution.

The event audit also shows concentration by era: 45 events occurred in the dot-com era, 23 around the GFC, and 17 post-2020. The full-period gain therefore still requires robustness testing rather than being accepted as a universal law. Segment tests already show the contextual layer helped strongly in the dot-com window, had essentially no effect in the GFC/COVID/inflation windows, and hurt post-2010 terminal wealth unless the shock override was present.

## Current research conclusion

The evidence supports a more nuanced hierarchy:

1. **100-DMA remains the hard market-defense baseline.**
2. **The tested macro-confirmed exit and macro-conditioned re-entry architectures are rejected.**
3. **Immediate re-entry remains the default when evaluating the plain DMA strategy.**
4. **Fed context is not discarded.** The specific contextual Fed exception + shock override is promising and materially outperformed the plain 100-DMA baseline in the full-history synthetic test.
5. **The contextual three-layer rule is not yet production-ready.** It needs robustness tests across eras, realistic costs/execution, and independent implementation/replay validation before it can replace the simpler baseline.
6. The shock-only **re-entry** veto remains rejected; that is a different mechanism from the shock override used inside the contextual exception.

The next stage should therefore validate the promising three-layer architecture rather than broadly rejecting macro. In parallel, continue realistic execution/cost robustness and paper-trading-readiness work on the strongest candidate(s).
