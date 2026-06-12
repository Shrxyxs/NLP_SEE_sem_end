import os
import numpy as np
import matplotlib.pyplot as plt

# Data
prompts = [f"Prompt {i}" for i in range(1, 9)]
bert_qwk = [0.7930, 0.6840, 0.6620, 0.7250, 0.7810, 0.7650, 0.7920, 0.6340]
muril_qwk = [0.4556, 0.3388, 0.4372, 0.5717, 0.6373, 0.4819, 0.6570, 0.3699]

x = np.arange(len(prompts))
width = 0.35

# Styles
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

# Harmonized colors
# Sleek indigo/blue for English BERT, vibrant emerald/teal for Kannada MuRIL
rects1 = ax.bar(x - width/2, bert_qwk, width, label='BERT Base (English)', color='#3F51B5', edgecolor='none', alpha=0.9)
rects2 = ax.bar(x + width/2, muril_qwk, width, label='MuRIL Base (Kannada)', color='#009688', edgecolor='none', alpha=0.9)

# Labels & title
ax.set_ylabel('Quadratic Weighted Kappa (QWK)', fontsize=12, fontweight='bold', labelpad=10)
ax.set_title('Bilingual Essay Scoring Model Comparison (QWK per Prompt)', fontsize=14, fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(prompts, fontsize=10, fontweight='bold')
ax.set_ylim(0.0, 1.0)

# Legend details
ax.legend(frameon=True, facecolor='white', edgecolor='#E0E0E0', fontsize=10, loc='upper right')

# Grid customization
ax.grid(True, linestyle='--', alpha=0.5, color='#CCCCCC')
ax.set_axisbelow(True)

# Add values above bars
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, color='#333333', fontweight='semibold')

autolabel(rects1)
autolabel(rects2)

# Save to artifacts directory
artifact_dir = r"C:\Users\nisha\.gemini\antigravity-ide\brain\0c5050c8-4df9-4824-a985-d99368ce56f4"
os.makedirs(artifact_dir, exist_ok=True)
save_path = os.path.join(artifact_dir, "model_comparison.png")

plt.tight_layout()
plt.savefig(save_path, bbox_inches='tight')
print(f"Graph successfully generated and saved to: {save_path}")
