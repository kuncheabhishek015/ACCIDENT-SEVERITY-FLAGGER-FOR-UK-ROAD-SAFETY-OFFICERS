"""
Data Visualization Engine
Generates publication-grade statistical charts and EDA visualizations using Matplotlib & Seaborn
for collision severity analysis, contingency heatmaps, speed limit distributions, and model performance.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any

from src.decoder import Stats19Decoder


class DataVisualizationEngine:
    """Generates and saves exploratory data visualization charts for academic reports."""

    def __init__(self, df: pd.DataFrame, output_dir: str = 'reports/visualizations'):
        self.df = df
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set Seaborn aesthetics
        sns.set_theme(style='darkgrid')
        plt.rcParams['font.sans-serif'] = 'Helvetica'
        plt.rcParams['axes.edgecolor'] = '#cccccc'

    def plot_severity_distribution(self) -> str:
        """Plots 3-class collision severity counts and binary target distribution."""
        fig, ax = plt.subplots(1, 2, figsize=(12, 5))
        
        # Chart 1: Original 3-class STATS19 severity
        severity_counts = self.df['severity_label'].value_counts()
        colors = ['#10b981', '#f59e0b', '#ef4444']
        ax[0].bar(severity_counts.index, severity_counts.values, color=colors, edgecolor='black', alpha=0.85)
        ax[0].set_title('DfT STATS19 Collision Severity Counts', fontsize=12, fontweight='bold')
        ax[0].set_ylabel('Number of Collisions')
        for i, v in enumerate(severity_counts.values):
            ax[0].text(i, v + 1000, f"{v:,}", ha='center', fontweight='bold', fontsize=9)
            
        # Chart 2: Binary is_severe target distribution
        severe_counts = self.df['is_severe'].map({0: 'Slight (0)', 1: 'Fatal/Serious (1)'}).value_counts()
        ax[1].pie(severe_counts.values, labels=severe_counts.index, autopct='%1.1f%%',
                   colors=['#10b981', '#ef4444'], startangle=140, explode=(0, 0.08),
                   textprops={'fontsize': 11, 'weight': 'bold'})
        ax[1].set_title('Binary Severe Collision Target (26.2% Severe)', fontsize=12, fontweight='bold')

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'severity_distribution.png')
        plt.savefig(filepath, dpi=300)
        plt.close()
        return filepath

    def plot_weather_light_risk_heatmap(self) -> str:
        """Plots heatmap of severe collision rates across Weather vs. Light conditions."""
        pivot = self.df.pivot_table(
            index='weather_label', 
            columns='light_label', 
            values='is_severe', 
            aggfunc='mean'
        ) * 100
        
        plt.figure(figsize=(10, 6))
        sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd', cbar_kws={'label': 'Severe Collision Rate (%)'}, linewidths=0.5)
        plt.title('Severe Collision Rate (%) across Weather & Light Conditions', fontsize=13, fontweight='bold', pad=12)
        plt.ylabel('Weather Condition')
        plt.xlabel('Light Condition')
        plt.xticks(rotation=30, ha='right')
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'weather_light_heatmap.png')
        plt.savefig(filepath, dpi=300)
        plt.close()
        return filepath

    def plot_speed_limit_risk_distribution(self) -> str:
        """Plots severe collision proportion by Speed Limit."""
        grouped = self.df.groupby('speed_limit')['is_severe'].agg(['count', 'mean']).reset_index()
        grouped['severe_pct'] = grouped['mean'] * 100
        
        fig, ax1 = plt.subplots(figsize=(10, 5))
        
        color = '#0284c7'
        ax1.set_xlabel('Speed Limit (mph)', fontweight='bold')
        ax1.set_ylabel('Total Collisions', color=color, fontweight='bold')
        ax1.bar(grouped['speed_limit'].astype(str), grouped['count'], color=color, alpha=0.6, width=0.5)
        ax1.tick_params(axis='y', labelcolor=color)
        
        ax2 = ax1.twinx()  
        color = '#ef4444'
        ax2.set_ylabel('Severe Rate (%)', color=color, fontweight='bold')
        ax2.plot(grouped['speed_limit'].astype(str), grouped['severe_pct'], color=color, marker='o', linewidth=2.5, markersize=8)
        ax2.tick_params(axis='y', labelcolor=color)
        
        plt.title('Collision Count & Severe Risk Rate by Speed Limit', fontsize=13, fontweight='bold')
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'speed_limit_risk_distribution.png')
        plt.savefig(filepath, dpi=300)
        plt.close()
        return filepath

    def generate_all_visualizations(self) -> Dict[str, str]:
        """Executes all data visualization chart generation."""
        f1 = self.plot_severity_distribution()
        f2 = self.plot_weather_light_risk_heatmap()
        f3 = self.plot_speed_limit_risk_distribution()
        print(f"Generated 3 publication-grade visualization plots in {self.output_dir}/")
        return {
            'severity_distribution': f1,
            'weather_light_heatmap': f2,
            'speed_limit_risk': f3
        }


if __name__ == '__main__':
    decoder = Stats19Decoder('dft-road-casualty-statistics-collision-2025.csv')
    df = decoder.decode()
    viz = DataVisualizationEngine(df)
    paths = viz.generate_all_visualizations()
    print("Visualizations Created:", paths)
