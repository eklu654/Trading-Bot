# TQQQ Three-Layer Actual-ETF Validation — 2026-10-07

## Result

The frozen three-layer architecture **does not improve the actual TQQQ implementation** over the hard 100-DMA baseline.

Signals are generated from QQQ/VIX/Fed, but returns are taken from actual TQQQ adjusted open/close data. This is the important validation because the earlier $200B+ result used a synthetic daily-reset 3x QQQ series.

| Strategy | Ending balance | CAGR | Max DD |
|---|---:|---:|---:|
| **Actual TQQQ + 100-DMA** | **$93.89M** | **80.66%** | **-35.38%** |
| Actual TQQQ + Fed-conditioned exception | $80.55M | 79.00% | -41.92% |
| Actual TQQQ + three-layer shock override | $91.18M | 80.34% | **-35.38%** |
| Actual TQQQ buy-and-hold | $2.10M | 43.76% | -81.66% |

Period: actual TQQQ history from 2010 through 2026-10-05, $5,000 start, no costs/cash yield.

## Cost stress

At fixed per-transition costs:

| Cost | 100-DMA | Three-layer |
|---:|---:|---:|
| 0 bps | $93.89M | $91.18M |
| 5 bps | $85.64M | $83.08M |
| 10 bps | $78.11M | $75.70M |
| 25 bps | $59.26M | $57.24M |
| 50 bps | $37.36M | $35.89M |

The three-layer variant remains slightly behind the simple 100-DMA strategy at every tested cost level.

## Decision

This is a major robustness finding.

The synthetic three-layer result remains interesting as a research signal, but it **must not be promoted to the production candidate** based on synthetic results alone. On actual TQQQ, the hard 100-DMA strategy is superior.

The current strongest actual-ETF candidate is therefore:

**TQQQ → 100-DMA hard exit → immediate re-entry → no macro veto.**

The Fed/shock research is retained because macro context may still become useful as part of a future broader regime/AI decision layer, but this frozen three-layer rule has now failed the actual-ETF validation hurdle.
