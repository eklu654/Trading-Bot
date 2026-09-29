# Account-Size Sensitivity Research

The project now treats account size as an empirical variable rather than assuming that $2,000 is either sufficient or insufficient.

The same candidate trade ledger is replayed at:

- $2,000
- $5,000
- $10,000

using the same 50% maximum BPR/NLV research ceiling and both conservative and midpoint fill variants.

## Why $5,000 matters

The prior $2,000 broad-sideways replay rejected all 929 candidate entries because the modeled BPR requirement exceeded the account's $1,000 maximum allocation.

The observed historical BPR distribution for those candidates was approximately:

- minimum: $1,378
- 10th percentile: $2,426
- median: $4,047
- 75th percentile: $5,937
- 90th percentile: $8,152
- maximum: $11,082

At a 50% BPR ceiling:

| Starting NLV | Maximum modeled BPR |
|---:|---:|
| $2,000 | $1,000 |
| $5,000 | $2,500 |
| $10,000 | $5,000 |

This makes $5,000 a materially different feasibility test: it crosses the historical minimum BPR requirement and reaches roughly the lower tail of the observed BPR distribution. It does **not** imply that the strategy becomes profitable or robust at $5,000.

The completed replay is the authority for the actual acceptance rate and P/L at each account size.

## Required comparison

For each NLV and fill model, record:

- candidate entries;
- accepted entries;
- rejected entries;
- rejection reasons;
- realized P/L;
- final NLV;
- maximum drawdown;
- peak BPR;
- BPR/NLV;
- stress loss/NLV;
- stale-mark exposure;
- trade count;
- opportunity utilization.

The key metric is not merely whether one trade can fit. It is the percentage of the historical opportunity set the account can actually express while respecting all hard constraints.

## Important interpretation

A larger account may improve opportunity access without improving the underlying strategy's expectancy.

Conversely, a strategy may have positive unconstrained trade economics while remaining unusable at a given account size.

Both dimensions must therefore be measured independently.
