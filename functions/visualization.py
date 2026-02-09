import numpy as np
import matplotlib.pyplot as plt
from config import ALL_PROGRESSION_VALUES_MARTIN, SIMPLE_PROGRESSION_CATEGORIES_URI, FINE_PROGRESSION_CATEGORIES_URI , ALL_PROGRESSION_VALUES_URI, OUTPUT_PATH

def plot_progression_heatmap(composer, transition_probs, categories, vmax=None):
    ann_threshold=0.01   # only label cells >= this
    cats = list(categories)
   
    data = transition_probs.loc[cats, cats].to_numpy()
    vmax = np.max(data)
    fig, ax = plt.subplots(figsize=(21, 21))
    im = ax.imshow(data, aspect="equal", cmap="Reds", vmin=0.0, vmax=vmax)

    ax.set_xticks(np.arange(len(cats)))
    ax.set_yticks(np.arange(len(cats)))
    ax.set_xticklabels(cats)
    ax.set_yticklabels(cats)
    ax.grid(which="minor", linewidth=0.3)

    ax.set_title(f"{composer}", fontsize=40)
    if categories == ALL_PROGRESSION_VALUES_URI:
        ax.set_xlabel("Next progression (No. of 5ths)", fontsize=30)
        ax.set_ylabel("Current progression (No. of 5ths)", fontsize=30)
    else:
        ax.set_xlabel("Next progression", fontsize=30)
        ax.set_ylabel("Current progression", fontsize=30)

    # Light grid for readability
    ax.set_xticks(np.arange(-.5, len(cats), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(cats), 1), minor=True)
    ax.grid(which="minor", linewidth=0.3)
    ax.tick_params(which="minor", bottom=False, left=False)
    plt.tick_params(axis='both', labelsize=26)  # x + y ticks

    coords = np.argwhere(data >= ann_threshold)

    for (i, j) in coords:
            ax.text(j, i, f"{data[i, j]:.2f}", ha="center", va="center", fontsize=24)

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_PATH}/img/{composer}.png")
    plt.close()


import numpy as np
import matplotlib.pyplot as plt
from config import (
    ALL_PROGRESSION_VALUES_MARTIN,
    SIMPLE_PROGRESSION_CATEGORIES_URI,
    FINE_PROGRESSION_CATEGORIES_URI,
    ALL_PROGRESSION_VALUES_URI,
    OUTPUT_PATH,
)

# TODO: GO THROUGH THIS ONE and adapt it
def plot_progression_heatmap_modified(
    composer: str,
    transition_matrix,
    categories,
    vmax=None,
    kind: str = "raw",   # "raw" | "row" | "joint"
    debug: bool = False,
):
    """
    kind:
      - "raw":  no normalization assumption
      - "row":  each row should sum to 1 (row-conditional transition probs)
      - "joint": entire matrix should sum to 1 (unconditional joint probs)
    """
    ann_threshold = 0.005
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
    # shown_mass = float(data[data >= ann_threshold].sum())
    # hidden_mass = float(data[data < ann_threshold].sum())
    # print(f"[{composer}] shown_mass={shown_mass:.4f} hidden_mass={hidden_mass:.4f} (threshold={ann_threshold})")
    if debug:
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

    vmax = np.max(data) if vmax is None else vmax
    fig, ax = plt.subplots(figsize=(21, 21))
    im = ax.imshow(data, aspect="equal", cmap="Reds", vmin=0.0, vmax=vmax)

    ax.set_xticks(np.arange(len(cats)))
    ax.set_yticks(np.arange(len(cats)))
    ax.set_xticklabels(cats)
    ax.set_yticklabels(cats)

    ax.set_title(f"{composer}", fontsize=40)
    if categories == ALL_PROGRESSION_VALUES_URI:
        ax.set_xlabel("Next progression (No. of 5ths)", fontsize=30)
        ax.set_ylabel("Current progression (No. of 5ths)", fontsize=30)
    else:
        ax.set_xlabel("Next progression", fontsize=30)
        ax.set_ylabel("Current progression", fontsize=30)

    # Light grid
    ax.set_xticks(np.arange(-.5, len(cats), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(cats), 1), minor=True)
    ax.grid(which="minor", linewidth=0.3)
    ax.tick_params(which="minor", bottom=False, left=False)
    plt.tick_params(axis="both", labelsize=26)

    coords = np.argwhere(data >= ann_threshold)
    for (i, j) in coords:
        ax.text(j, i, f"{data[i, j]:.2f}", ha="center", va="center", fontsize=24)

    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_PATH}/img/{composer}.png")
    plt.close()


def save_heatmaps(composer, cond_probs, uncond_probs, cond_probs_fine, uncond_probs_fine, cond_trim, uncond_trim, diff_cats_trim, weight_uncond_probs, uncond_weight_joint_martin):
    # Save heatmaps for progression probabilities
    plot_progression_heatmap(f"{composer}_COND", cond_probs, categories=SIMPLE_PROGRESSION_CATEGORIES_URI)
    plot_progression_heatmap(f"{composer}_UNCOND", uncond_probs, categories=SIMPLE_PROGRESSION_CATEGORIES_URI)
    plot_progression_heatmap(f"{composer}_FINE_COND", cond_probs_fine, categories=FINE_PROGRESSION_CATEGORIES_URI)
    plot_progression_heatmap(f"{composer}_FINE_UNCOND", uncond_probs_fine, categories=FINE_PROGRESSION_CATEGORIES_URI)
    plot_progression_heatmap(f"{composer}_DIFF_COND", cond_trim, categories=diff_cats_trim)
    plot_progression_heatmap(f"{composer}_DIFF_UNCOND", uncond_trim, categories=diff_cats_trim)
    #plot_progression_heatmap_modified(f"{composer}_WEIGHT_UNCOND_URI", weight_uncond_probs, categories=ALL_PROGRESSION_VALUES_URI, kind="joint", debug=True)
    plot_progression_heatmap_modified(f"{composer}_WEIGHT_UNCOND_MARTIN", uncond_weight_joint_martin, categories=ALL_PROGRESSION_VALUES_MARTIN, kind="joint")



# def composer_progression_percentage_heatmap(df_plot, label_cols= PROGRESSION_CATEGORIES):
#     # Heatmap (composers x labels) with annotations
#     data = df_plot[label_cols].to_numpy()
#     composers = df_plot["composer"].tolist()

#     fig, ax = plt.subplots(figsize=(6.8, 4.6))
#     im = ax.imshow(data, aspect="auto")

#     ax.set_xticks(np.arange(len(label_cols)))
#     ax.set_xticklabels(label_cols)
#     ax.set_yticks(np.arange(len(composers)))
#     ax.set_yticklabels(composers)

#     ax.set_title("Progression label shares (heatmap)")
#     cbar = fig.colorbar(im, ax=ax)
#     cbar.set_label("Share (0..1)")

#     # annotate each cell
#     for i in range(data.shape[0]):
#         for j in range(data.shape[1]):
#             ax.text(j, i, f"{data[i, j]*100:.1f}%", ha="center", va="center", fontsize=9)

#     plt.tight_layout()

#     out2 = Path("output/composer_progression_heatmap.png")
#     fig.savefig(out2, dpi=210)
