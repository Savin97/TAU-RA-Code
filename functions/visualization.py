# visualization.py
import numpy as np
import matplotlib.pyplot as plt
from config import OUTPUT_PATH

def plot_heatmap(system,
    composer: str,
    graph_title,
    filename:str,
    transition_matrix,
    categories,
    vmax=None,
    kind: str = "raw",   # "raw" | "row" | "joint",
    debug: bool = False
    ):
    """
    kind:
      - "raw":  no normalization assumption
      - "row":  each row should sum to 1 (row-conditional transition probs)
      - "joint": entire matrix should sum to 1 (unconditional joint probs)
    """
    ann_threshold = 0.001
    cats = list(categories)

    # Build EXACT grid for what you are plotting
    sub = transition_matrix.reindex(index=cats, columns=cats, fill_value=0.0).astype(float)

    # ---- IMPORTANT FIX ----
    # If this is supposed to be a joint distribution, normalize *the plotted grid*.
    if kind == "joint":
        total = float(sub.to_numpy().sum())
        if total > 0.0:
            sub = sub / total

    # If this is supposed to be row-conditional, normalize rows of the plotted grid.
    if kind == "row":
        denom = sub.sum(axis=1).replace(0.0, 1.0)
        sub = sub.div(denom, axis=0)

    data = sub.to_numpy()
    shown_mass = float(data[data >= ann_threshold].sum())
    hidden_mass = float(data[data < ann_threshold].sum())

    if debug:
        print(f"[{composer}] shown_mass={shown_mass:.4f} hidden_mass={hidden_mass:.4f} (threshold={ann_threshold})")
        total = float(data.sum())
        print(f"[{composer}] kind={kind} total_sum={total}")

        if kind == "joint":
            # Expect ~1
            print(f"  joint_sum (expect ~1): {total}")
        elif kind == "row":
            # Expect each non-empty row ~1
            row_sums = data.sum(axis=1)
            nonempty = row_sums > 0
            if nonempty.any():
                max_err = float(np.max(np.abs(row_sums[nonempty] - 1.0)))
                print(f"  row_max_err (expect small): {max_err}")
            else:
                print("  (all rows empty)")
        # kind == "raw": no assumptions

    vmax = np.max(data)
    if vmax <= 0:
        vmax = 1.0  # or return early with a warning
    fig, ax = plt.subplots(figsize=(21, 21))

    zero_masked = np.ma.masked_where(data == 0.0, data)
    cmap = plt.cm.Reds.copy() # Reds for normal values #type:ignore
    cmap.set_bad(color="lightgray")  # color for masked values (zeroes)

    im = ax.imshow(zero_masked, aspect="equal", cmap=cmap, vmin=0.0, vmax=vmax)

    ax.set_xticks(np.arange(len(cats)))
    ax.set_yticks(np.arange(len(cats)))
    ax.set_xticklabels(cats)
    ax.set_yticklabels(cats)

    ax.set_title(f"{composer} {graph_title}", fontsize=40)

    # Light grid
    ax.set_xticks(np.arange(-.5, len(cats), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(cats), 1), minor=True)
    ax.grid(which="minor", linewidth=0.3)
    ax.tick_params(which="minor", bottom=False, left=False)
    plt.tick_params(axis="both", labelsize=26)

    coords = np.argwhere(data >= ann_threshold)
    for (i, j) in coords:
        ax.text(j, i, f"{data[i, j]:.3f}", ha="center", va="center", fontsize=14)

    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_PATH}/{system}/img/{filename}.png")
    plt.close()

def plot_stacked_bars(stacked_df, composer_order):
    # x labels with years
    x_labels = [
        f"{composer}\n{int(year)}"
        for composer, year in zip(
            composer_order["composer"],
            composer_order["composer_mid_year"]
        )
    ]
    # Add "Other" = remaining probability mass
    stacked_df["Other"] = 1 - stacked_df.sum(axis=1)

    # numerical safety (avoid tiny negatives due to float errors)
    stacked_df["Other"] = stacked_df["Other"].clip(lower=0)

    # ------------------------------
    # Handling colors
    # ------------------------------
    color_map = { 
        "0": "#BBBBBB",
        "1": "#DD8452",
        "2": "#55A868",
        "Other": "#000000"
    }
    # generate random colors for anything not in the map
    rng = np.random.default_rng(40)  # fixed seed → consistent colors

    def random_color():
        return rng.random(3,)  # RGB tuple

    colors = [
        color_map[col] if col in color_map else random_color()
        for col in stacked_df.columns
    ]

    ax = stacked_df.plot(
        kind="bar",
        stacked=True,
        figsize=(30, 8),
        color=colors
    )
    stacked_df = stacked_df[sorted(stacked_df.columns)]

    ax.set_xlabel("Composer (mid-life year)")
    ax.set_ylabel("Probability")
    ax.set_title("Top 5 Root Progressions per Composer")

    # ------------------------------
    # Add labels inside each segment
    # ------------------------------
    for container in ax.containers:
        for bar in container:
            height = bar.get_height()

            if height < 0.02:   # skip tiny segments (avoid clutter)
                continue

            x = bar.get_x() + bar.get_width() / 2
            y = bar.get_y() + height / 2

            ax.text(
                x,
                y,
                f"{height:.2f}",   # show probability
                ha="center",
                va="center",
                fontsize=8
            )
    # The last container corresponds to the last column ("Other")
    other_container = ax.containers[-1]

    for bar in other_container:
        bar.set_hatch("//")          # diagonal lines
        bar.set_facecolor("none")    # transparent fill
        bar.set_edgecolor("black")   # visible hatch lines
        ax.set_xticklabels(x_labels, rotation=30, ha="right")

    ax.legend(title="Root progression", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_PATH}/chronoligcal_root_prog_graph.png")
    plt.close()
    print(f"Chronoligcal Root Progression Graph Created in: '{OUTPUT_PATH}/chronoligcal_root_prog_graph.png'")
    return 