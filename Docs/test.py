
@st.cache_data(show_spinner="Running pipeline…")
def get_earnings_df(use_cached_eps: bool = True) -> pd.DataFrame:
    """
    Calls your engine and returns the final dashboard dataframe.

    Assumes run_pipeline(...) returns a DataFrame with at least:
      Date, Stock, Risk Score, Recommendation,
      Excessive Move, No Reaction, Reaction Divergence,
      Muted Response, Extreme Volatility, divergence_alert
    """
    df = run_pipeline(use_cached_eps=use_cached_eps)

    # Ensure Date is datetime if present
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Build any_alert convenience column
    alerts_cols = [
        "Excessive Move",
        "No Reaction",
        "Reaction Divergence",
        "Muted Response",
        "Extreme Volatility",
        "divergence_alert",
    ]
    for c in alerts_cols:
        if c not in df.columns:
            df[c] = pd.NA

    # any_alert: True if any of the alert columns is non-empty / non-zero
    df["any_alert"] = False

    # Excessive Move – treat anything that isn't the safe text as alert
    if "Excessive Move" in df.columns:
        em = df["Excessive Move"].fillna("")
        safe_text = "No - Within normal range."
        df["any_alert"] |= ~em.str.contains(safe_text, na=False)

    # No Reaction, Reaction Divergence, Muted Response, divergence_alert:
    # anything non-null counts
    for col in ["No Reaction", "Reaction Divergence", "Muted Response", "divergence_alert"]:
        if col in df.columns:
            df["any_alert"] |= df[col].notna()

    # Extreme Volatility – non-zero numeric counts as alert
    if "Extreme Volatility" in df.columns:
        ev = pd.to_numeric(df["Extreme Volatility"], errors="coerce")
        df["any_alert"] |= ev.fillna(0) != 0

    return df