# Options Portfolio Allocation Methodology Research

**Status:** Research reconciliation — not frozen  
**Last reviewed:** 2026-09-27

## Purpose

This document reconciles the separate tastytrade/tastylive evidence now available for:

- VIX-based aggregate allocation;
- undefined-risk vs. defined-risk allocation;
- per-trade buying-power limits;
- beta-weighted Delta;
- diversification/correlation;
- and reserve capital.

The goal is to determine which historical guidance can become a deterministic rule in this project and which must remain an experimental parameter.

## 1. VIX-based aggregate allocation

The project has direct screenshot evidence from a Trade Talk presentation showing:

| VIX | Maximum account allocation |
|---|---:|
| 10–15 | 25% |
| 15–20 | 30% |
| 20–30 | 35% |
| 30–40 | 40% |
| >40 | 50% |

This screenshot is preserved in the user's Library as **Screenshot_20210413-175727.png**. fileciteturn2file0

tastylive identifies the underlying *How to Build a Portfolio Using Complex Options Strategies* presentation as part of its educational video catalog. citeturn3search0

The project records this as **historical documented guidance**, not automatically as a current universal 2026 requirement.

## 2. Undefined-risk vs. defined-risk allocation

A 2019 tastylive Reserve Capital episode states that its portfolio-allocation framework allocated:

- 75% of buying power to undefined-risk strategies;
- 25% to defined-risk strategies.

That same source states per-trade limits of:

- 3%–5% for undefined-risk trades;
- 0.5%–2% for defined-risk trades.

It also explicitly says that more buying power should be allocated to products when VIX is higher. citeturn5search0

These figures are useful evidence of a historical framework, but they should not be assumed to be unchanged current policy.

## 3. Newer capital-allocation guidance

A 2024 tastylive portfolio-risk article describes a prudent capital-allocation range of 25%–50%, with a 75% maximum cap, and warns that BPR can expand under market pressure. citeturn5search4

This is important because it overlaps with, but does not exactly reproduce, the older VIX table.

The project therefore needs to treat the historical sources as a sequence of documented frameworks rather than pretending they are one timeless rule.

## 4. Proposed reconciliation model

The implementation should represent capital allocation as a hierarchy of constraints.

### Layer 1 — Aggregate allocation ceiling

Determine the maximum options-portfolio allocation from the selected VIX schedule.

Historical candidate:

- 10–15 → 25%
- 15–20 → 30%
- 20–30 → 35%
- 30–40 → 40%
- >40 → 50%

### Layer 2 — Strategy-type budget

Within the aggregate ceiling, maintain separate budgets for:

- undefined-risk positions;
- defined-risk positions.

The historical 75/25 split should be tested rather than hard-coded as current doctrine.

### Layer 3 — Individual position limit

Each candidate position must satisfy its own BPR/risk budget.

The historical 2019 guidance gives 3%–5% for undefined-risk and 0.5%–2% for defined-risk trades. These are research inputs, not yet frozen project rules. citeturn5search0

### Layer 4 — Portfolio directional exposure

Use beta-weighted Delta with SPY as the benchmark for aggregate directional exposure. Current tastylive material explicitly describes beta-weighted Delta using SPY as a portfolio-risk measure. citeturn5search4

The project still needs to define the numerical neutrality band.

### Layer 5 — Correlation/concentration

Do not treat different tickers as automatically diversified.

Current tastylive guidance explicitly identifies correlation risk as a separate portfolio risk and discusses monitoring correlation between positions. citeturn5search4

### Layer 6 — Dynamic BPR stress

The system must continuously re-evaluate actual BPR rather than only the BPR at entry.

Current tastylive small-account research documents substantial BPR expansion after adverse price movement and increased implied volatility. citeturn0search2

## 5. Critical distinction: allocation is permission, not deployment

A VIX allocation ceiling does not mean:

> "At VIX 25, deploy exactly 35%."

It means:

> "Under this framework, the options portfolio may use up to 35% of account capital, subject to all other risk constraints."

This distinction is mandatory for the bot.

The strategy must be allowed to remain below the ceiling when suitable trades are unavailable or other constraints prevent deployment.

## 6. $2,000 account implications

The historical VIX schedule produces:

| VIX | Maximum allocation | $2,000 account |
|---|---:|---:|
| 10–15 | 25% | $500 |
| 15–20 | 30% | $600 |
| 20–30 | 35% | $700 |
| 30–40 | 40% | $800 |
| >40 | 50% | $1,000 |

The historical per-trade limits produce much smaller nominal amounts:

### Undefined risk

- 3% = $60
- 5% = $100

### Defined risk

- 0.5% = $10
- 2% = $40

This creates an immediate implementation problem: one option contract can consume more BPR than these percentages permit.

Therefore the project cannot simply copy the historical percentages and assume they are executable in a $2,000 account.

## 7. Small-account exception must be explicit

The project's previously discussed 5%–7% small-account allowance is **not** an official tastytrade rule.

It is a project-specific candidate designed to address whole-contract granularity.

It must be tested against:

- actual BPR;
- maximum loss;
- BPR expansion;
- portfolio Delta;
- correlation;
- assignment risk;
- account drawdown.

The bot must never increase a position merely because the desired percentage is otherwise impossible.

## 8. Research questions to resolve

### A. Does the VIX table apply to all option strategies?

The available evidence does not establish this conclusively.

### B. Does the 75/25 undefined/defined-risk split sit inside the VIX allocation?

This is the most important structural question.

### C. Is the 75/25 split a target, maximum, or illustrative portfolio composition?

The source wording needs further reconstruction from the original presentation/context.

### D. What exact BPR definition should the bot use?

The execution broker's buying-power calculation may differ by account type and position structure.

### E. What beta-weighted Delta band constitutes "neutral"?

The benchmark should initially be SPY, but the numerical band remains unresolved.

### F. How should correlation be measured?

Candidate methods:

- rolling Pearson correlation;
- beta/factor exposure;
- sector concentration;
- stress correlation.

### G. How should existing positions behave after VIX allocation changes?

Project decision already established:

**Regime changes do not automatically liquidate existing options positions.**

The allocation ceiling governs new risk unless an independent hard-risk rule requires action.

## 9. Preliminary risk-engine hierarchy

The research now supports this conceptual hierarchy:

1. Account-level emergency/loss controls
2. Assignment/expiration safeguards
3. Aggregate BPR hard ceiling
4. VIX-derived allocation ceiling
5. Strategy-type allocation budget
6. Individual position BPR/risk ceiling
7. Portfolio beta-weighted Delta limits
8. Correlation/concentration limits
9. Entry-quality rules
10. AI opportunity ranking

AI remains below every hard risk constraint.

## 10. Next experiments

The first backtesting matrix should compare:

### Allocation model

- historical VIX 25/30/35/40/50 schedule;
- fixed 25%;
- fixed 35%;
- fixed 50%;
- 2024-style 25%–50% with 75% hard cap.

### Strategy mix

- undefined-risk only;
- defined-risk only;
- historical 75/25 mix;
- project-specific alternatives.

### Position sizing

- historical 3%–5% undefined-risk range;
- historical 0.5%–2% defined-risk range;
- project 5%–7% small-account exception;
- contract-granularity-aware sizing.

All variants must use identical market data and execution assumptions.

## Current decision

The project now has enough evidence to stop treating VIX allocation as an unsupported idea.

However, we do **not** yet have enough evidence to freeze the complete options portfolio methodology.

The next step is to reconstruct the original Trade Talk presentation's surrounding rules and reconcile them with newer tastylive risk-management material before implementation.
