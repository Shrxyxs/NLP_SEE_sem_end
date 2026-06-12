import os
import matplotlib.pyplot as plt
import numpy as np

# Hardware profiles
systems = ['Nishan U Shetty\nRyzen 9 + RTX 3050', 'Shreyas Bharadwaj\nRyzen 5 + RTX 3050', 'Preetham R\nApple M4 Pro']
power_draw = [110, 120, 50]  # Watts
carbon_footprint = [75.1, 82.0, 34.2]  # grams of CO2 for a 5-epoch run (50 mins)

x = np.arange(len(systems))
width = 0.35

# Style setup
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig, ax1 = plt.subplots(figsize=(9, 5.5), dpi=300)

# Dual Y-axes for Power and Carbon footprint
color = '#3F51B5'
ax1.set_xlabel('Team Member Hardware Profiles', fontsize=12, fontweight='bold', labelpad=12)
ax1.set_ylabel('Active Power Draw (Watts)', color=color, fontsize=12, fontweight='bold')
rects1 = ax1.bar(x - width/2, power_draw, width, label='Active Power Draw (W)', color=color, alpha=0.85)
ax1.tick_params(axis='y', labelcolor=color)
ax1.set_ylim(0, 150)

ax2 = ax1.twinx()  
color = '#E91E63'
ax2.set_ylabel('Carbon Emissions (g CO2 eq.)', color=color, fontsize=12, fontweight='bold')
rects2 = ax2.bar(x + width/2, carbon_footprint, width, label='5-Epoch Training Emissions (g CO2)', color=color, alpha=0.85)
ax2.tick_params(axis='y', labelcolor=color)
ax2.set_ylim(0, 100)

# Annotations
def autolabel(rects, ax, unit):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}{unit}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='semibold')

autolabel(rects1, ax1, 'W')
autolabel(rects2, ax2, 'g')

plt.title('Hardware Energy Consumption & Environmental Footprint Comparison\n(Bilingual AES Training Load)', fontsize=13, fontweight='bold', pad=15)
ax1.set_xticks(x)
ax1.set_xticklabels(systems, fontsize=10, fontweight='semibold')
ax1.grid(True, linestyle='--', alpha=0.3)

# Legend combining both axes
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines + lines2, labels + labels2, loc='upper right', frameon=True, facecolor='white')

# Save to artifacts directory
artifact_dir = r"C:\Users\nisha\.gemini\antigravity-ide\brain\0c5050c8-4df9-4824-a985-d99368ce56f4"
os.makedirs(artifact_dir, exist_ok=True)
save_path = os.path.join(artifact_dir, "hardware_comparison.png")

plt.tight_layout()
plt.savefig(save_path, bbox_inches='tight')
print(f"Hardware comparison graph saved to: {save_path}")
