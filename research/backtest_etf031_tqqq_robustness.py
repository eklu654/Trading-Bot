def dma_next_open_returns(frame: pd.DataFrame, cost_bps: float) -> pd.Series:
    """200-DMA/cash with prior-close signal and next-open execution.

    A signal observed at yesterday's close is acted on at today's open. On
    entry days, only today's open-to-close move is captured; on exit days,
    only the prior close-to-today open move is captured. When already held,
    the full adjusted close-to-close move is captured. This keeps the full
    input date range while avoiding same-close execution or look-ahead.

    Raw opens are scaled by adj_close / close so splits and distributions are
    represented consistently with the adjusted-close total-return series.
    """
    adjusted_open = frame["open"].astype(float) * (
        frame["adj_close"].astype(float) / frame["close"].astype(float)
    )
    adjusted_close = frame["adj_close"].astype(float)
    ma = adjusted_close.rolling(MA_WINDOW).mean()
    held = (adjusted_close.shift(1) >= ma.shift(1)).fillna(False)
    previous_held = held.shift(1).fillna(False)

    entry_day = held & ~previous_held
    holding_day = held & previous_held
    exit_day = ~held & previous_held

    out = pd.Series(0.0, index=frame.index, dtype=float)
    out.loc[entry_day] = adjusted_close.loc[entry_day] / adjusted_open.loc[entry_day] - 1.0
    out.loc[holding_day] = adjusted_close.loc[holding_day] / adjusted_close.shift(1).loc[holding_day] - 1.0
    out.loc[exit_day] = adjusted_open.loc[exit_day] / adjusted_close.shift(1).loc[exit_day] - 1.0

    turnover = held.astype(float).diff().abs().fillna(held.astype(float))
    return out - turnover * (cost_bps / 10000.0)
