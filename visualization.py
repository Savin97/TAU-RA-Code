import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from config import PROGRESSION_CATEGORIES, OUTPUT_PATH

OUTPUT = Path(OUTPUT_PATH)

def plot_progression_heatmap(composer, transition_probs, categories=PROGRESSION_CATEGORIES, vmax=None):
    cats = list(categories)
    data = transition_probs.loc[cats, cats].to_numpy()

    vmax = np.max(data)


    fig, ax = plt.subplots(figsize=(6, 4), dpi=200)
    im = ax.imshow(data, aspect="equal", cmap="Reds", vmin=0.0, vmax=vmax)

    ax.set_xticks(np.arange(len(cats)))
    ax.set_yticks(np.arange(len(cats)))
    ax.set_xticklabels(cats)
    ax.set_yticklabels(cats)

    ax.set_xlabel("Next progression")
    ax.set_ylabel("Current progression")
    ax.set_title(f"{composer}")

    for i in range(len(cats)):
        for j in range(len(cats)):
            ax.text(j, i, f"{data[i, j]:.3f}", ha="center", va="center")

    fig.colorbar(im, ax=ax)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_PATH}/{composer}.png")


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
#     fig.savefig(out2, dpi=200)
