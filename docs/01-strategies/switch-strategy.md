# SWITCH-001 — Regime-Switching Strategy

**Status:** Research specification — candidate classifier, not yet production-frozen.

## 1. Purpose

SWITCH-001 determines which strategy is eligible to initiate new risk:

- **ETF-001:** leveraged ETF trend-following.
- **OPTIONS-001:** rules-based short-premium / defined-risk options portfolio.
- **CASH:** no new risk when neither strategy has an acceptable opportunity.

The intended portfolio behavior is that **ETF-001 remains the default / majority regime**. OPTIONS-001 becomes more eligible when the market is **sideways/choppy** or **turbulent/high-volatility**, subject to its own IVR, liquidity, sizing, and portfolio-risk constraints.

SWITCH-001 is an eligibility and allocation controller. It does not override hard risk controls and does not force-liquidate existing OPTIONS-001 positions merely because the regime changes.

---

## 2. Research conclusion

The research does **not** support using VIX alone as the regime switch.

VIX measures expected 30-day S&P 500 volatility from SPX options. It is useful as a market-wide volatility input, but it is not a direct measure of trend direction or trend quality. Research comparing VIX with realized volatility also shows that implied and realized volatility can diverge materially, particularly during stress. Therefore VIX should be treated as a **volatility-state feature**, not as the complete market-regime classifier.

Trend-following research provides evidence for persistent price trends across multiple markets and horizons, while research on volatility-conditioned trend following suggests that volatility information can alter the usefulness of trend signals but does not universally improve them. The project should therefore combine trend and volatility information rather than encode a rule such as `VIX > X => OPTIONS`.

Sources:
- Moskowitz, Ooi & Pedersen, *Time Series Momentum*.
- Hurst, Ooi & Pedersen, *A Century of Evidence on Trend-Following Investing*.
- CME/Institute for Financial Research material on trend following and volatility/correlation regimes.
- Fidelity's current ADX explanation for trend-strength interpretation.
- Perry Kaufman's Efficiency Ratio material for separating trend efficiency from price noise.

---

## 3. Three-state market model

SWITCH-001 should classify the broad market into one of three primary states:

### TRENDING / NORMAL

Characteristics:

- price is directionally established;
- long-term trend is intact;
- trend strength is sufficient;
- path efficiency is not excessively noisy;
- volatility is not in an acute shock state.

Primary action:

- **ETF-001 eligible.**
- OPTIONS-001 receives low priority unless a separate options opportunity is unusually attractive.
- Preserve cash according to ETF-001's own capital/risk rules.

### SIDEWAYS / CHOPPY

Characteristics:

- price repeatedly crosses or hugs its long-term trend;
- long-term moving-average slope is weak/flat;
- directional trend strength is weak;
- price path is inefficient/noisy;
- volatility is not necessarily high.

Primary action:

- reduce or suspend new ETF-001 exposure;
- **OPTIONS-001 becomes eligible**, provided its volatility/opportunity and portfolio-risk rules pass;
- CASH remains valid if options opportunities do not pass their own filters.

This state is important because a leveraged trend strategy can repeatedly enter and exit around a range without receiving the sustained directional movement it requires.

### TURBULENT / HIGH VOLATILITY

Characteristics:

- realized volatility is elevated or rapidly increasing;
- VIX is elevated relative to its own recent history and/or rising rapidly;
- large daily ranges or volatility shocks are occurring;
- trend may be strong, weak, or rapidly changing.

Primary action:

- reduce/suspend new leveraged ETF exposure according to ETF-001's hard risk rules;
- **OPTIONS-001 becomes eligible**, but only when IVR, liquidity, structure, BPR/max-loss, delta, correlation, and execution constraints pass;
- CASH remains valid when volatility is too disorderly for acceptable execution.

High volatility is therefore an **eligibility condition**, not an automatic instruction to sell premium.

---

## 4. Feature set

The first deterministic classifier should use a small number of interpretable features.

### 4.1 Long-term trend position

For each ETF-001 benchmark:

- `close / SMA200 - 1`
- `SMA200 slope`
- number of consecutive closes above/below SMA200

The existing ETF-001 rule remains authoritative for ETF entry/exit:

> Sell when price moves below the 200-day moving average; rebuy only after price has remained above it for a full week.

The classifier should **not replace this rule**. Instead, it adds information about whether the broader market is trending cleanly enough for the strategy to be favored.

### 4.2 Trend strength

Use **ADX(14)** and its direction.

ADX measures trend strength rather than direction; DMI+/DMI- can provide direction. Fidelity describes >25 as a commonly used indication of a stronger trend and <20 as commonly interpreted as weak/no trend, while noting that these are conventions rather than guarantees.

Candidate research buckets:

- ADX < 20: weak trend / likely non-trending
- 20–25: transition
- >25: stronger trend
- rising ADX: strengthening
- falling ADX: weakening

These thresholds are **research parameters**, not frozen production rules.

### 4.3 Efficiency / noise

Use Kaufman Efficiency Ratio (ER):

`ER_N = abs(Close_t - Close_{t-N}) / sum(abs(Close_i - Close_{i-1}))`

ER approaches 1 when the price path is directionally efficient and approaches 0 when the path contains substantial back-and-forth movement.

This is valuable because **volatility and noise are not the same thing**. A market can have high volatility while still moving efficiently in one direction; conversely, a market can have substantial movement but end near where it started.

Candidate windows:

- ER(10)
- ER(20)
- ER(40)

Thresholds should be selected from out-of-sample testing or rolling percentiles rather than assumed universal constants.

### 4.4 Realized volatility

Calculate annualized realized volatility from daily returns using multiple horizons:

- RV(10)
- RV(20)
- RV(60)

Use both:

- current percentile versus rolling historical RV;
- short-term change in RV.

The purpose is to distinguish ordinary volatility from a **volatility acceleration/shock**.

### 4.5 VIX state

Track:

- VIX level;
- VIX percentile over a rolling history;
- 5-day VIX change;
- VIX relative to a moving average;
- optionally VIX term structure when reliable data are available.

Do not hardcode `VIX > 28` or `VIX > 30` as the regime definition at this stage.

A fixed absolute threshold may be retained as a separately tested **ETF safety overlay**, because it corresponds to the user's original risk-control concept. It should not be allowed to masquerade as the complete regime classifier.

### 4.6 Optional volatility-of-volatility input

VVIX measures implied volatility of VIX options and can provide information about expected volatility of volatility. It is potentially useful for identifying disorderly volatility conditions, but it adds complexity and should initially be an optional research feature rather than a required input.

---

## 5. Initial deterministic classifier

The first implementation should avoid machine learning.

Calculate a normalized score for each component and produce three interpretable sub-scores:

### TrendScore

Inputs:

- SMA200 position
- SMA200 slope
- ADX level/direction
- ER

### ChopScore

Inputs:

- distance from SMA200
- SMA200 slope near zero
- ADX weak/falling
- ER low
- repeated SMA200 crossings

### TurbulenceScore

Inputs:

- VIX percentile
- VIX rate of change
- RV percentile
- RV acceleration
- optionally VVIX / VIX term structure

Conceptually:

`Regime = TURBULENT` if TurbulenceScore exceeds its tested emergency/transition threshold.

Otherwise:

`Regime = TRENDING` if TrendScore exceeds its tested trend threshold.

Otherwise:

`Regime = SIDEWAYS`.

This ordering is intentional: an acute volatility shock should not be classified as ordinary sideways trading simply because trend strength has temporarily disappeared.

---

## 6. Use continuous eligibility, not a binary switch

The controller should ultimately produce allocation/eligibility outputs rather than only a label.

Example interface:

```text
regime
trend_score
chop_score
turbulence_score
etf_eligibility
options_eligibility
cash_preference
confidence
reason_codes[]
```

The first research version can still use discrete states, but the architecture should support continuous values later.

Example conceptual behavior:

| State | ETF-001 | OPTIONS-001 | Cash |
|---|---|---|---|
| Trending/Normal | High priority | Low priority | Reserve |
| Sideways/Choppy | Reduced/blocked for new risk | High priority | Reserve |
| Turbulent/High Vol | Reduced/blocked for new risk | High priority, subject to stricter execution/risk gates | Potentially higher |

**These are eligibility relationships, not final allocation percentages.**

The exact allocation curve must be backtested.

---

## 7. Breadth across the three ETF sleeves

ETF-001 contains three leveraged ETFs:

- TQQQ
- SPXL
- SOXL

The regime engine should not assume that all three have identical trend states.

Each should have a benchmark-specific trend state:

- TQQQ → Nasdaq-100 / QQQ trend
- SPXL → S&P 500 / SPY trend
- SOXL → semiconductor benchmark (candidate: SOXX or another explicitly selected benchmark)

The switch can then distinguish:

- **broad trend:** most/all sleeves trending;
- **partial trend:** only some sleeves trending;
- **broad deterioration:** most/all sleeves weak;
- **sector-specific deterioration:** one sleeve fails while others remain valid.

This is preferable to treating a single VIX value as a universal signal.

---

## 8. Hysteresis and confirmation

Regime classifiers can otherwise oscillate rapidly.

The implementation should therefore test confirmation rules such as:

- require 2 consecutive daily classifications before entering a new regime;
- require 3 consecutive days before returning to the prior regime;
- or use a score band with separate enter/exit thresholds.

Example:

`TRENDING -> SIDEWAYS` at ChopScore >= X

but

`SIDEWAYS -> TRENDING` only when ChopScore <= Y, where Y < X.

This prevents small indicator fluctuations from causing unnecessary strategy switching.

These values remain research parameters.

---

## 9. Relationship to existing ETF-001 rules

The original ETF strategy should remain intact:

1. 200-day moving-average exit.
2. One full week above the 200-day moving average before re-entry.
3. VIX safety overlay remains a candidate, not a frozen rule.

SWITCH-001 does not weaken these rules.

Instead:

- ETF-001 determines whether an individual leveraged ETF position is permitted.
- SWITCH-001 determines whether the market environment makes ETF-001 the preferred source of **new** risk.
- Risk controls can override both.

This separation is important. A regime change should not create contradictory instructions such as "the switch wants options" while the ETF's own hard exit rule has not yet triggered.

---

## 10. AI's role

AI may eventually assist with:

- regime classification;
- anomaly detection;
- feature discovery;
- candidate ranking;
- identifying relationships between VIX, realized volatility, trend persistence, and ETF performance.

AI must **not**:

- override 200-DMA exits;
- override the one-week ETF re-entry rule;
- override options max-loss/BPR limits;
- override concentration/delta/correlation constraints;
- invent a trade when no deterministic candidate passes;
- disable emergency exits.

The production system should always be able to explain a regime decision using deterministic feature values and reason codes.

---

## 11. Backtest required before freezing thresholds

The classifier must be tested against the actual objective of this project:

> Keep ETF-001 active for the majority of normal market time while reducing exposure during conditions where leveraged trend-following historically suffers and making OPTIONS-001 eligible when sideways/choppy or turbulent conditions provide acceptable opportunities.

Required comparisons:

1. Original ETF-001 without SWITCH-001.
2. ETF-001 + VIX-only switch.
3. ETF-001 + trend/volatility classifier.
4. ETF-001 + trend/volatility classifier + ER.
5. ETF-001 + trend/volatility classifier + ER + ADX.
6. Optional AI-assisted classifier, evaluated only after deterministic baselines.

Metrics:

- total return;
- CAGR;
- maximum drawdown;
- Sharpe;
- Sortino;
- realized volatility;
- percentage of time in ETF regime;
- percentage of time in options-eligible regime;
- percentage of time in cash;
- regime transition count;
- average regime duration;
- ETF whipsaw count;
- ETF time below/above 200-DMA;
- options opportunity acceptance/rejection rate;
- options constraint-infeasibility rate;
- transaction costs/slippage;
- performance by VIX percentile;
- performance by realized-volatility percentile;
- performance by trend/chop state.

The key metric is **not simply highest return**. The classifier must demonstrate whether it improves the specific failure modes it was designed to address without creating excessive switching or destroying the intended majority-ETF behavior.

---

## 12. Research parameters to sweep

Do not optimize a single parameter set and declare victory.

Test ranges for:

- SMA trend horizon: 100 / 150 / 200 / 250 days
- ADX window: 10 / 14 / 20
- ADX trend thresholds
- ER window: 10 / 20 / 40
- ER thresholds or rolling percentiles
- RV windows: 10 / 20 / 60
- VIX percentile windows
- VIX rate-of-change windows
- confirmation days
- hysteresis width
- turbulence thresholds
- ETF allocation curve
- options allocation curve.

All parameter selection must use time-ordered validation. Avoid look-ahead bias and avoid choosing thresholds from the same period used to report final performance.

---

## 13. Current project decision

**Adopt the following architecture for the next implementation phase:**

```text
Market Data
   |
   +--> Trend Features
   |      - SMA200 position
   |      - SMA200 slope
   |      - ADX
   |      - Efficiency Ratio
   |
   +--> Volatility Features
   |      - VIX level/percentile
   |      - VIX change
   |      - Realized volatility
   |      - Realized-volatility acceleration
   |
   v
SWITCH-001
   |
   +--> TRENDING/NORMAL ------> ETF-001 preferred
   |
   +--> SIDEWAYS/CHOPPY ------> OPTIONS-001 eligible
   |
   +--> TURBULENT/HIGH VOL ---> OPTIONS-001 eligible
   |                             + stricter execution/risk gates
   |
   +--> insufficient opportunity ----------------> CASH
   |
   v
Hard Risk Engine
   |
   v
Execution
```

This is the recommended **research architecture**, not yet the frozen production allocation rule.

## 14. Evidence and interpretation

### Verified evidence

- Time-series momentum/trend-following has been documented across many liquid futures markets and over long historical samples. citeturn1search1turn1search0
- Trend-following behavior varies with market volatility and correlation; high volatility alone does not guarantee a favorable trend environment. citeturn1search48turn1search50
- ADX is intended to measure trend strength rather than direction; commonly cited thresholds around 20/25 are conventions, not guarantees. citeturn0search7
- Kaufman's Efficiency Ratio is explicitly designed to distinguish efficient directional movement from noisy/back-and-forth movement. citeturn2search2turn2search0
- VIX and realized volatility can diverge, so VIX should not be treated as a perfect measure of current realized market turbulence. citeturn0search3
- Recent research continues to find that VIX regime classification is difficult because volatility is noisy, mean-reverting, autocorrelated, and affected by multiple market forces. citeturn0search9

### Project interpretation

The combination of trend position, trend strength, path efficiency, and volatility state is therefore a more defensible starting point for SWITCH-001 than a single VIX threshold.

### Not yet established

No threshold, weighting, allocation percentage, confirmation period, or exact regime transition rule should be considered validated until it survives the project's time-ordered backtests.

---

## 15. Next research step

The next step is **not more indicator shopping**.

It is to construct a historical regime-label dataset and test the candidate classifier against ETF-001's actual behavior.

Specifically:

1. obtain daily SPY, QQQ, semiconductor benchmark, VIX and required OHLC data;
2. calculate all candidate features without look-ahead;
3. generate candidate regime labels;
4. measure how ETF-001 historically behaves inside each label;
5. determine whether SIDEWAYS and TURBULENT labels actually correspond to the desired reduction in ETF exposure;
6. test whether OPTIONS-001 has enough viable opportunities in those same periods;
7. only then freeze thresholds and allocation curves.
