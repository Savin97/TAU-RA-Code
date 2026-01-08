import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from config import PROGRESSION_CATEGORIES, OUTPUT_PATH

OUTPUT = Path(OUTPUT_PATH)

def plot_progression_heatmap(composer, transition_probs, categories=PROGRESSION_CATEGORIES):
    cats = list(categories)
    data = transition_probs.loc[cats, cats].to_numpy()

    fig, ax = plt.subplots(figsize=(6, 4), dpi=200)
    im = ax.imshow(
        data,
        aspect="equal",
        cmap="Reds",   # red intensity colormap
        vmin=0.0,      # force 0 → white
        vmax=1.0       # optional but recommended for probabilities
    )

    # Axis labels
    ax.set_xticks(np.arange(len(cats)))
    ax.set_yticks(np.arange(len(cats)))
    ax.set_xticklabels(cats)
    ax.set_yticklabels(cats)

    ax.set_xlabel("Next progression")
    ax.set_ylabel("Current progression")
    ax.set_title(f"Transition probabilities of progression strength, {composer}")

    # Write probability values in each cell
    for i in range(len(cats)):
        for j in range(len(cats)):
            ax.text(
                j, i, f"{data[i, j]:.2f}",
                ha="center", va="center"
            )

    fig.colorbar(im, ax=ax)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_PATH}/{composer}.png")