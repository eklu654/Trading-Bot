"""Descriptive classification of frozen 100-DMA episodes by macro context.

This deliberately does not optimize thresholds. It reports continuous relationships
and coarse, predeclared policy-state groups so we can decide whether Fed context
contains explanatory information beyond the price-based 100-DMA exit.
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
INPUT = DATA / "tqqq_100dma_macro_episode_attribution.csv"


def main() -> None:
    ep = pd.read_csv(INPUT)
    if ep.empty:
        raise RuntimeError("No macro episode attribution rows found.")

    ep["negative"] = ep["bh_return_to_reentry"] < 0
    ep["large_loss"] = ep["bh_worst_return_during_episode"] <= -0.50

    # These are descriptive labels, not candidate trading thresholds.
    ep["policy_state"] = np.where(
        ep["fed_cycle_direction"].eq("tightening"),
        "tightening",
        np.where(ep["fed_cycle_direction"].eq("easing"), "easing", "unknown"),
    )

    # Compare outcomes by policy state only; do not optimize a boundary.
    state = (
        ep.groupby("policy_state", dropna=False)
        .agg(
            episodes=("exit_date", "size"),
            negative_episode_rate=("negative", "mean"),
            large_loss_episode_rate=("large_loss", "mean"),
            median_bh_return_to_reentry=("bh_return_to_reentry", "median"),
            mean_bh_return_to_reentry=("bh_return_to_reentry", "mean"),
            median_worst_interim_return=("bh_worst_return_during_episode", "median"),
            median_flat_days=("flat_trading_days", "median"),
            median_fed_target=("fed_target_at_exit", "median"),
            median_cycle_net_change=("fed_cycle_net_change", "median"),
            median_days_since_fed_move=("days_since_fed_move", "median"),
            median_curve_2s10s=("curve_2s10s_at_exit", "median"),
            median_curve_change_20d=("curve_change_20d_at_exit", "median"),
        )
        .reset_index()
    )

    numeric = [
        "fed_target_at_exit",
        "fed_cycle_net_change",
        "days_since_fed_move",
        "fed_moves_in_cycle",
        "fed_distance_from_cycle_peak",
        "fed_distance_from_cycle_trough",
        "curve_2s10s_at_exit",
        "curve_change_20d_at_exit",
        "dma_gap_at_exit",
        "dma_slope_20d_at_exit",
        "qqq_return_5d_at_exit",
        "qqq_return_20d_at_exit",
        "qqq_return_60d_at_exit",
        "qqq_realized_vol_20d_at_exit",
    ]
    targets = {
        "episode_return": "bh_return_to_reentry",
        "worst_interim_return": "bh_worst_return_during_episode",
        "flat_trading_days": "flat_trading_days",
    }
    correlations = []
    for col in numeric:
        x = pd.to_numeric(ep[col], errors="coerce")
        for target_name, target_col in targets.items():
            y = pd.to_numeric(ep[target_col], errors="coerce")
            mask = x.notna() & y.notna()
            if mask.sum() >= 3:
                correlations.append(
                    {
                        "feature": col,
                        "target": target_name,
                        "episodes": int(mask.sum()),
                        "pearson_corr": float(x[mask].corr(y[mask])),
                        "spearman_corr": float(
                            x[mask].rank().corr(y[mask].rank())
                        ),
                    }
                )
    corr = pd.DataFrame(correlations)

    # Crisis-era sanity table: major episodes should remain visible regardless of policy state.
    major = ep.loc[
        ep["bh_worst_return_during_episode"] <= -0.50,
        [
            "exit_date",
            "reentry_date",
            "flat_trading_days",
            "bh_return_to_reentry",
            "bh_worst_return_during_episode",
            "fed_target_at_exit",
            "fed_cycle_direction",
            "fed_cycle_net_change",
            "days_since_fed_move",
            "curve_2s10s_at_exit",
        ],
    ].sort_values("bh_worst_return_during_episode")

    DATA.mkdir(parents=True, exist_ok=True)
    state.to_csv(DATA / "tqqq_100dma_macro_policy_state_summary.csv", index=False)
    corr.to_csv(DATA / "tqqq_100dma_macro_feature_correlations.csv", index=False)
    major.to_csv(DATA / "tqqq_100dma_macro_major_loss_episodes.csv", index=False)

    print("\nPOLICY-STATE SUMMARY")
    print(state.to_string(index=False))
    print("\nFEATURE CORRELATIONS WITH EPISODE OUTCOMES")
    print(corr.to_string(index=False))
    print("\nMAJOR LOSS EPISODES (<= -50% WORST INTERIM RETURN)")
    print(major.to_string(index=False))
    print(f"\nEpisodes analyzed: {len(ep)}")


if __name__ == "__main__":
    main()
