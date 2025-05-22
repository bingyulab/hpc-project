import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

sns.set(style="whitegrid", font_scale=1.2)

latency_df = pd.read_csv("latency.csv")
bandwidth_df = pd.read_csv("bandwidth.csv")

latency_df['size'] = latency_df['size'].astype(int)
bandwidth_df['size'] = bandwidth_df['size'].astype(int)

specific_latency_size = 8192
specific_bandwidth_size = 1048576

# --- LATENCY LINE PLOT ---
plt.figure(figsize=(10, 6))
for placement, group in latency_df.groupby("placement"):
    group_sorted = group.sort_values("size")
    specific_val = group[group["size"] == specific_latency_size]["latency_us"].mean()
    if not pd.isna(specific_val):
        label = f"{placement} : {specific_val:.2f} us"
    else:
        label = placement
    plt.plot(group_sorted["size"], group_sorted["latency_us"], label=label, marker='o')

plt.xscale("log")
plt.yscale("log")
plt.xlabel("Message Size (Bytes)")
plt.ylabel("Latency (us)")
plt.title("OSU-Eessi Latency vs Message Size")
plt.xticks([2**i for i in range(0, 14)], labels=[2**i for i in range(0, 14)], rotation=45)
plt.legend(title="Placement")
plt.tight_layout()
plt.savefig("latency_plot.png", dpi=300)
plt.close()

# --- BANDWIDTH LINE PLOT ---
plt.figure(figsize=(10, 6))
for placement, group in bandwidth_df.groupby("placement"):
    group_sorted = group.sort_values("size")
    specific_val = group[group["size"] == specific_bandwidth_size]["bandwidth_MBps"].mean()
    if not pd.isna(specific_val):
        label = f"{placement} : {specific_val:.2f} MB/s"
    else:
        label = placement
    plt.plot(group_sorted["size"], group_sorted["bandwidth_MBps"], label=label, marker='o')

plt.xscale("log")
plt.xlabel("Message Size (Bytes)")
plt.ylabel("Bandwidth (MB/s)")
plt.title("OSU-Eessi Bandwidth vs Message Size")
plt.xticks([2**i for i in range(0, 21)], labels=[2**i for i in range(0, 21)], rotation=45)
plt.legend(title="Placement")
plt.tight_layout()
plt.savefig("bandwidth_plot.png", dpi=300)
plt.close()

# --- LATENCY BAR PLOT: Average vs 8192 ---
lat_pivot_avg = pd.pivot_table(
    latency_df,
    values="latency_us",
    index="placement",
    aggfunc="mean"
).squeeze()

lat_specific = latency_df[latency_df['size'] == specific_latency_size]
lat_specific_values = lat_specific.groupby('placement')['latency_us'].mean().squeeze()

lat_combined = pd.DataFrame({
    'Average Latency (us)': lat_pivot_avg,
    f'Latency at {specific_latency_size} (us)': lat_specific_values
})

ax1 = lat_combined.plot(kind='bar', figsize=(12, 8), width=0.8)
plt.title(f"OSU-Eessi Latency: Average vs Specific at {specific_latency_size}")
plt.ylabel("Latency (us)")

# Add text labels on top of bars
for container in ax1.containers:
    ax1.bar_label(container, fmt='%.2f', padding=3)

plt.tight_layout()
plt.savefig("latency_avg_and_specific.png")
plt.close()

# --- BANDWIDTH BAR PLOT: Average vs 1048576 ---
bw_pivot_avg = pd.pivot_table(
    bandwidth_df,
    values="bandwidth_MBps",
    index="placement",
    aggfunc="mean"
).squeeze()

bw_specific = bandwidth_df[bandwidth_df['size'] == specific_bandwidth_size]
bw_specific_values = bw_specific.groupby('placement')['bandwidth_MBps'].mean().squeeze()

bw_combined = pd.DataFrame({
    'Average Bandwidth (MB/s)': bw_pivot_avg,
    f'Bandwidth at {specific_bandwidth_size} (MB/s)': bw_specific_values
})

ax2 = bw_combined.plot(kind='bar', figsize=(12, 8), width=0.8)
plt.title(f"OSU-Eessi Bandwidth: Average vs Specific at {specific_bandwidth_size}")
plt.ylabel("Bandwidth (MB/s)")

# Add text labels on top of bars
for container in ax2.containers:
    ax2.bar_label(container, fmt='%.2f', padding=3)

plt.tight_layout()
plt.savefig("bandwidth_avg_and_specific.png")
plt.close()

print("Analysis complete.")
