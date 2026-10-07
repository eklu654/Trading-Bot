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

## Research conclusion

The evidence now supports a simple hierarchy:

1. **100-DMA is the hard market-defense trigger.**
2. **Initial exits are never canceled by macro conditions.**
3. **Immediate re-entry is strongly favored.**
4. Macro/Fed information remains useful for analysis and future decision-support, but it should not currently veto the proven re-entry mechanism.
5. Volatility/shock logic should not be added to re-entry solely to reduce drawdown; the tested version sacrificed substantial terminal wealth without improving max drawdown.

The next research stage should therefore move away from increasingly restrictive re-entry delays and toward validation of the already-proven hard 100-DMA architecture, including realistic execution/cost robustness and eventual paper-trading readiness.
