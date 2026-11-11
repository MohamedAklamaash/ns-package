from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from hypernet.experiments.percolation.analysis import merge_synthetic, tuning_instances
from hypernet.experiments.percolation.figures import ordered_settings
from hypernet.experiments.percolation.grids import MAP_FULL

STYLE = {
    "oracle": {"marker": "o", "linestyle": "-", "color": "0.0", "label": "oracle (uses ground truth)"},
    "chosen": {"marker": "s", "linestyle": "--", "color": "0.35", "label": "our rule"},
    "default": {"marker": "^", "linestyle": ":", "color": "0.6", "label": "paper default"},
}
TITLES = {"large": "large-edge variant", "small": "small-edge variant"}

def pretty(name):
    intra, rand = name.split("_")
    return f"intra {intra[1]}-{intra[3]}, random {rand[1]}-{rand[3]}"

results = Path("../results")
frame = merge_synthetic([pd.read_csv(results / "e1_check.csv"), pd.read_csv(results / "e2_map.csv")])
instances = tuning_instances(frame)
names = ordered_settings(instances, MAP_FULL.settings)
figure, axes = plt.subplots(2, len(names), figsize=(3.4 * len(names), 6.0), squeeze=False, sharey=True)
for col, name in enumerate(names):
    for row, method in enumerate(("large", "small")):
        axis = axes[row, col]
        cell = instances[(instances["setting"] == name) & (instances["method"] == method)]
        means = cell.groupby("noise_fraction")[[f"{p}_ecs" for p in STYLE]].mean()
        for pick, style in STYLE.items():
            axis.plot(means.index, means[f"{pick}_ecs"], markersize=4, **style)
        axis.set_title(f"{pretty(name)}\n{TITLES[method]}", fontsize=8)
        axis.set_ylim(-0.02, 1.02)
        axis.grid(alpha=0.3, color="0.8")
        axis.set_xlabel("noise fraction p", fontsize=8)
axes[0, 0].set_ylabel("mean ECS", fontsize=8)
axes[1, 0].set_ylabel("mean ECS", fontsize=8)
handles, labels = axes[0, 0].get_legend_handles_labels()
figure.legend(handles, labels, loc="lower center", ncol=3, fontsize=9)
figure.tight_layout(rect=(0, 0.06, 1, 1))
out = Path("../slides_figures"); out.mkdir(exist_ok=True)
figure.savefig(out / "rule_slide.png", dpi=200)
print("saved")
