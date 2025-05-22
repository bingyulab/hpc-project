#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import seaborn as sns
from matplotlib.gridspec import GridSpec

# Ensure output directory exists
os.makedirs('../docs/imgs', exist_ok=True)

# Function to parse pipe-delimited OSU benchmark logs
def parse_osu_logs(log_path):
    try:
        # Read the pipe-delimited file
        df = pd.read_csv(log_path, sep='|')
        
        # Clean column names by stripping whitespace
        df.columns = df.columns.str.strip()
        
        # Create a copy for modification
        result_df = df.copy()
        
        # Determine metric type based on unit and create metric column
        if 'bandwidth_unit' in df.columns:
            # For rows with bandwidth unit (MB/s)
            result_df['metric'] = 'bandwidth'
            result_df['value'] = pd.to_numeric(result_df['bandwidth_value'], errors='coerce')
            result_df['unit'] = result_df['bandwidth_unit']
        
        # Select only the columns we need
        result_df = result_df[['result', 'system', 'binary_source', 'placement_type', 'metric', 'value', 'unit']]
        
        # Add cluster label based on filename
        cluster = "iris" if "iris" in log_path else "aion"
        result_df['cluster'] = cluster
        
        # To handle test types based on unit (for visualization)
        # Set rows with "us" unit to be latency measurements 
        mask_latency = result_df['unit'] == 'us'
        result_df.loc[mask_latency, 'metric'] = 'latency'       
        
        return result_df
        
    except Exception as e:
        print(f"Error parsing {log_path}: {str(e)}")
        return pd.DataFrame() 

# Paths to log files
iris_log = "perflogs/iris/batch/OSUPlacementTest.log"
aion_log = "perflogs/aion/batch/OSUPlacementTest.log"

# Parse data from both clusters
iris_results = parse_osu_logs(iris_log)
aion_results = parse_osu_logs(aion_log)

# Combine results
df = pd.concat([iris_results, aion_results])
df.to_csv('./perflogs/osu_results_combined.csv', index=False)
# Check if we have data
if df.empty:
    print("No data found in log files. Please check paths and log content.")
    exit(1)

# Print basic statistics to verify data
print(f"Total results: {len(df)}")
print("\nResults by cluster:")
print(df['cluster'].value_counts())

print("\nResults by placement type:")
print(df['placement_type'].value_counts())

print("\nResults by binary source:")
print(df['binary_source'].value_counts())

print("\nResults by metric:")
print(df['metric'].value_counts())

# Set up plotting style
plt.style.use('ggplot')
sns.set_palette("Set2")
plt.rcParams.update({'font.size': 12})
# Define consistent order for placement types and binary sources
placement_order = ['same_numa', 'diff_numa_same_socket', 'diff_socket_same_node', 'diff_node']
binary_order = ['local', 'easybuild', 'eessi']
placement_labels = {
    'same_numa': 'Same NUMA',
    'diff_numa_same_socket': 'Diff NUMA',
    'diff_socket_same_node': 'Diff Socket',
    'diff_node': 'Diff Node'
}

# Create 2x2 grid of plots - bandwidth and latency, for each cluster
fig, axs = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('OSU Micro-Benchmark Performance by Placement and Binary Source', fontsize=16)

# Plot bandwidth for iris (top-left)
bw_iris = df[(df['cluster'] == 'iris') & (df['metric'] == 'bandwidth')].copy()
if not bw_iris.empty:
    pivot = pd.pivot_table(bw_iris, values='value', index='placement_type', 
                          columns='binary_source', aggfunc='mean')
    # Reorder index based on our desired order
    pivot = pivot.reindex(placement_order)
    pivot[binary_order].plot(kind='bar', ax=axs[0, 0], rot=0)
    axs[0, 0].set_title('Bandwidth on Iris')
    axs[0, 0].set_ylabel('Bandwidth (MB/s)')
    axs[0, 0].set_ylim(bottom=0)
    # Use the shorter labels from placement_labels
    axs[0, 0].set_xticklabels([placement_labels[p] for p in pivot.index])
    
# Plot bandwidth for aion (top-right)
bw_aion = df[(df['cluster'] == 'aion') & (df['metric'] == 'bandwidth')].copy()
if not bw_aion.empty:
    pivot = pd.pivot_table(bw_aion, values='value', index='placement_type', 
                          columns='binary_source', aggfunc='mean')
    pivot = pivot.reindex(placement_order)
    pivot[binary_order].plot(kind='bar', ax=axs[0, 1], rot=0)
    axs[0, 1].set_title('Bandwidth on Aion')
    axs[0, 1].set_ylabel('Bandwidth (MB/s)')
    axs[0, 1].set_ylim(bottom=0)
    # Use the shorter labels from placement_labels
    axs[0, 1].set_xticklabels([placement_labels[p] for p in pivot.index])

# Plot latency for iris (bottom-left)
lat_iris = df[(df['cluster'] == 'iris') & (df['metric'] == 'latency')].copy()
if not lat_iris.empty:
    pivot = pd.pivot_table(lat_iris, values='value', index='placement_type', 
                          columns='binary_source', aggfunc='mean')
    pivot = pivot.reindex(placement_order)
    pivot[binary_order].plot(kind='bar', ax=axs[1, 0], rot=0)
    axs[1, 0].set_title('Latency on Iris')
    axs[1, 0].set_ylabel('Latency (μs)')
    axs[1, 0].set_ylim(bottom=0)
    # Use the shorter labels from placement_labels
    axs[1, 0].set_xticklabels([placement_labels[p] for p in pivot.index])

# Plot latency for aion (bottom-right)
lat_aion = df[(df['cluster'] == 'aion') & (df['metric'] == 'latency')].copy()
if not lat_aion.empty:
    pivot = pd.pivot_table(lat_aion, values='value', index='placement_type', 
                          columns='binary_source', aggfunc='mean')
    pivot = pivot.reindex(placement_order)
    pivot[binary_order].plot(kind='bar', ax=axs[1, 1], rot=0)
    axs[1, 1].set_title('Latency on Aion')
    axs[1, 1].set_ylabel('Latency (μs)')
    axs[1, 1].set_ylim(bottom=0)
    # Use the shorter labels from placement_labels
    axs[1, 1].set_xticklabels([placement_labels[p] for p in pivot.index])

# Add legend and adjust layout
handles, labels = axs[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.06), ncol=3)

for ax in axs.flat:
    if hasattr(ax, 'legend_') and ax.legend_:
        ax.legend_.remove()  # Remove individual legends

plt.tight_layout(rect=[0, 0.08, 1, 0.95])
plt.savefig('../docs/imgs/osu_performance_comparison.png', dpi=300)

# Create heatmaps for a more intuitive visualization of placement impact
for cluster_name in df['cluster'].unique():
    # Bandwidth heatmap
    plt.figure(figsize=(10, 8))
    bw_data = df[(df['cluster'] == cluster_name) & (df['metric'] == 'bandwidth')].copy()
    if not bw_data.empty:
        pivot = pd.pivot_table(bw_data, values='value', 
                             index='placement_type', columns='binary_source',
                             aggfunc='mean')
        pivot = pivot.reindex(placement_order)
        
        sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlGnBu')
        plt.title(f'Bandwidth Performance Heatmap - {cluster_name.capitalize()}')
        plt.tight_layout()
        plt.savefig(f'../docs/imgs/bandwidth_heatmap_{cluster_name}.png', dpi=300)
        
    # Latency heatmap
    plt.figure(figsize=(10, 8))
    lat_data = df[(df['cluster'] == cluster_name) & (df['metric'] == 'latency')].copy()
    if not lat_data.empty:
        pivot = pd.pivot_table(lat_data, values='value', 
                             index='placement_type', columns='binary_source',
                             aggfunc='mean')
        pivot = pivot.reindex(placement_order)
        
        sns.heatmap(pivot, annot=True, fmt='.2f', cmap='YlOrRd_r')
        plt.title(f'Latency Performance Heatmap - {cluster_name.capitalize()}')
        plt.tight_layout()
        plt.savefig(f'../docs/imgs/latency_heatmap_{cluster_name}.png', dpi=300)

# IMPROVED PLOTS: Installation method comparison across clusters and placement types

# 1. Grouped bar chart for binary source comparison
for metric_name in ['bandwidth', 'latency']:
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{metric_name.capitalize()} Performance by Installation Method', fontsize=16)
    
    metric_data = df[df['metric'] == metric_name].copy()
    if metric_data.empty:
        continue
    
    # Use a subplot for each placement type
    for i, placement in enumerate(placement_order):
        row, col = divmod(i, 2)
        ax = axes[row, col]
        
        # Filter data for this placement type
        place_data = metric_data[metric_data['placement_type'] == placement].copy()
        if place_data.empty:
            continue
            
        # Create grouped bar chart
        pivot = pd.pivot_table(place_data, values='value', 
                             columns='cluster', index='binary_source',
                             aggfunc='mean')
        
        colors = ['#1f77b4', '#ff7f0e']  # Blue for iris, orange for aion
        pivot.plot(kind='bar', ax=ax, rot=0, color=colors)
        
        ax.set_title(f'{placement_labels[placement]}')
        if metric_name == 'bandwidth':
            ax.set_ylabel('Bandwidth (MB/s)')
        else:
            ax.set_ylabel('Latency (μs)')
        ax.set_ylim(bottom=0)
        
        # Add value labels on top of bars
        for container in ax.containers:
            ax.bar_label(container, fmt='%.1f', fontsize=9)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(f'../docs/imgs/{metric_name}_by_installation.png', dpi=300)

# 2. Radar chart to visualize placement impact
for metric_name in ['bandwidth', 'latency']:
    metric_data = df[df['metric'] == metric_name].copy()
    if metric_data.empty:
        continue
        
    # Create a figure with multiple radar plots - one for each binary source
    fig = plt.figure(figsize=(15, 10))
    fig.suptitle(f'{metric_name.capitalize()} by Process Placement', fontsize=16)
    
    for i, binary in enumerate(binary_order):
        # Create radar chart in a grid
        ax = plt.subplot(1, 3, i+1, polar=True)
        
        # Filter data for this binary source
        bin_data = metric_data[metric_data['binary_source'] == binary].copy()
        if bin_data.empty:
            continue
            
        # Create pivot table with all placement types
        pivot = pd.pivot_table(bin_data, values='value', 
                             columns='cluster', index='placement_type',
                             aggfunc='mean')
        
        # Ensure all placement types are included
        for placement in placement_order:
            if placement not in pivot.index:
                pivot.loc[placement] = np.nan
                
        # Reindex to ensure consistent order
        pivot = pivot.reindex(placement_order)
        
        # Number of categories
        N = len(placement_order)
        
        # Create radar angles
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Close the loop
        
        # Plot for each cluster
        for col, color in zip(pivot.columns, ['b', 'r']):
            values = pivot[col].tolist()
            values += values[:1]  # Close the loop
            
            # Plot values
            ax.plot(angles, values, color=color, linewidth=2, label=col)
            ax.fill(angles, values, color=color, alpha=0.25)
        
        # Set radar chart labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([placement_labels[p] for p in placement_order])
        ax.set_title(f'{binary.capitalize()}')
        
        # Add legend
        ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.tight_layout()
    plt.savefig(f'../docs/imgs/{metric_name}_radar_chart.png', dpi=300)

# 3. Comprehensive comparison across all dimensions
for metric_name in ['bandwidth', 'latency']:
    metric_data = df[df['metric'] == metric_name].copy()
    if metric_data.empty:
        continue
    
    # Create a figure with GridSpec for flexible layout
    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(2, 2, figure=fig)
    
    # Main plot - all combinations
    ax_main = fig.add_subplot(gs[0, :])
    
    # Create a grouped bar chart with hierarchical indexing
    pivot = pd.pivot_table(metric_data, values='value', 
                         columns=['cluster'], 
                         index=['placement_type', 'binary_source'],
                         aggfunc='mean')
    
    # Reindex to ensure consistent order
    idx = pd.MultiIndex.from_product([placement_order, binary_order], 
                                   names=['placement_type', 'binary_source'])
    pivot = pivot.reindex(idx)
    
    # Plot
    pivot.plot(kind='bar', ax=ax_main)
    
    # Format main plot
    ax_main.set_title(f'Complete {metric_name.capitalize()} Comparison')
    ax_main.set_ylabel(f'{metric_name.capitalize()} {"(MB/s)" if metric_name=="bandwidth" else "(μs)"}')
    ax_main.set_xticklabels([f"{placement_labels[p]}\n{b}" for p, b in pivot.index])
    
    # Bottom left - efficiency ratio plot (iris vs aion)
    ax_ratio = fig.add_subplot(gs[1, 0])
    
    # Calculate ratio between clusters
    if 'iris' in pivot.columns and 'aion' in pivot.columns:
        ratio = pivot['iris'] / pivot['aion']
        ratio.plot(kind='bar', ax=ax_ratio, color='purple')
        ax_ratio.set_title('Iris/Aion Performance Ratio')
        ax_ratio.set_ylabel('Ratio')
        ax_ratio.axhline(y=1, linestyle='--', color='black', alpha=0.5)
        ax_ratio.set_xticklabels([f"{placement_labels[p]}\n{b}" for p, b in ratio.index], rotation=90)
    
    # Bottom right - mean performance by binary source
    ax_binary = fig.add_subplot(gs[1, 1])
    binary_means = pd.pivot_table(metric_data, values='value', 
                                columns='cluster', index='binary_source',
                                aggfunc='mean')
    binary_means.plot(kind='bar', ax=ax_binary)
    ax_binary.set_title('Average Performance by Binary Source')
    ax_binary.set_ylabel(f'{metric_name.capitalize()} {"(MB/s)" if metric_name=="bandwidth" else "(μs)"}')
    
    # Add value labels
    for container in ax_binary.containers:
        ax_binary.bar_label(container, fmt='%.1f')
    
    plt.tight_layout()
    plt.savefig(f'../docs/imgs/{metric_name}_comprehensive.png', dpi=300)

print("\nAnalysis complete. Enhanced plots saved to ../docs/imgs/ directory.")