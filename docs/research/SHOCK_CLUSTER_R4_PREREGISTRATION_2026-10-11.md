# Shock-Cluster Re-entry Gate Preregistration — 2026-10-11

## Motivation
R3's SMA-confirmed staging failed to improve downside metrics and was rejected. Do not tune it. The next distinct hypothesis is that repeated shocks in a short window—not the age of a crash—can identify persistent stress, while a single shock followed by a V-shaped recovery should retain B0's fast recovery behavior.

## Fixed candidate R4
- Preserve B0 unchanged outside a defensive episode.
- A shock is a QQQ adjusted-close daily return <= -4.5%.
- Mark an episode as clustered stress if at least 2 such shock days occur in the trailing 20 sessions by the time B0's +10% recovery threshold is reached. If another shock occurs while defensive, update the running low and cluster status.
- If the episode is not clustered, re-enter 100% at B0's existing +10% rebound trigger (no added delay).
- If clustered, re-enter 50% when the +10% rebound threshold is reached. Retain 50% through renewed shocks and reset the running low. Restore 100% only when QQQ closes above its 20-session SMA and is still at least 10% above the current running low.
- Signals use close-known data and execute at next TQQQ open. No look-ahead or same-close fills.
- No threshold, window, exposure, or SMA tuning in this run.

## Comparison and stop rule
Compare R4 against B0/R1/R2/R2P/R3 on the same frozen QQQ/TQQQ snapshot, actual TQQQ dates, $5,000 initial capital, and 0/10/25/50 bps per exposure change. Unit tests and causal accounting invariants must pass.
Reject R4 if it does not materially improve downside metrics while preserving most B0 terminal wealth, or if improvement comes only from one event. Do not refine the 20-session cluster window or 20-session SMA after seeing results. If it fails, stop adding signal variants and evaluate a structural risk-budget design instead.

This is not a test of the 2000 crash: TQQQ did not exist then. Any pre-inception test must be a separately labeled daily-reset simulation on underlying index data.
