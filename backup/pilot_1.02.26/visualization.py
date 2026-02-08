import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from config import SIMPLE_PROGRESSION_CATEGORIES, OUTPUT_PATH, ROOT_DIFF_VALUES

OUTPUT = Path(OUTPUT_PATH)

def plot_progression_heatmap(composer, transition_probs, categories, vmax=None):
    ann_threshold=0.01   # only label cells >= this
    cats = list(categories)
   
    data = transition_probs.loc[cats, cats].to_numpy()

    vmax = np.max(data)
    fig, ax = plt.subplots(figsize=(21, 21))

    # if categories == ROOT_DIFF_VALUES:
    #     fig, ax = plt.subplots(figsize=(8, 6), dpi=400)

    # else:
    #     fig, ax = plt.subplots(figsize=(6, 4), dpi=210)
    im = ax.imshow(data, aspect="equal", cmap="Reds", vmin=0.0, vmax=vmax)

    ax.set_xticks(np.arange(len(cats)))
    ax.set_yticks(np.arange(len(cats)))
    ax.set_xticklabels(cats)
    ax.set_yticklabels(cats)
    ax.grid(which="minor", linewidth=0.3)

    ax.set_title(f"{composer}", fontsize=40)
    if categories == ROOT_DIFF_VALUES:
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
    plt.savefig(f"{OUTPUT_PATH}/{composer}.png")
    plt.close()


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
