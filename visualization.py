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
