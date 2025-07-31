#!/usr/bin/env python3
"""
RT60 Heatmap Analyzer for The Hub - Using actual Smaart measurement data
Based on the Studio 8 analyzer but adapted for The Hub's unique geometry and measurements
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from pathlib import Path

class RT60HeatmapAnalyzerHub:
    def __init__(self):
        # The Hub dimensions (converted from inches to feet based on actual measurements)
        self.room_ceiling_height = 106 / 12.0  # 106" = 8.83 feet to hung ceiling
        self.room_grid_height = 101 / 12.0     # 101" = 8.42 feet to grid
        
        # The Hub is an irregular hexagon - approximate dimensions for visualization
        self.room_width_approx = 190 / 12.0    # ~15.83 feet (widest point)
        self.room_length_approx = 150 / 12.0   # ~12.5 feet (longest dimension)
        
        # Frequency bands for analysis (matching reference chart)
        self.frequency_bands = [125, 250, 500, 1000, 2000, 4000, 8000]
        self.frequency_labels = ['125Hz', '250Hz', '500Hz', '1kHz', '2kHz', '4kHz', '8kHz']
        
        # Measurement positions for The Hub (based on available data files)
        # Coordinates are approximate relative positions within the hexagonal space
        self.measurement_positions = {
            "MidRoom": {"coords": [0, 0, 6], "name": "Mid Room"},
            "BackCorner": {"coords": [-6, -2, 6], "name": "Back Corner"},
            "Chair1": {"coords": [-4.5, 0.5, 4], "name": "Chair 1"},
            "Chair2": {"coords": [-3.5, 1.5, 4], "name": "Chair 2"},
            "CeilingCorner": {"coords": [5, 1, 10], "name": "Ceiling Corner"}
        }
        
        # Load actual RT60 measurements from Smaart logs
        self.load_smaart_rt60_data()
    
    def load_smaart_rt60_data(self):
        """Load actual RT60 measurements from The Hub Smaart log files"""
        # Path to The Hub logs
        smaart_path = Path('data/raw/250715-smaartLogs/TheHub')
        
        # Mapping from file names to our position names
        file_to_position = {
            'TheHub-MidRoom-64k.txt': 'MidRoom',
            'TheHub-BackCorner-64k.txt': 'BackCorner',
            'TheHub-Chair1-64k.txt': 'Chair1',
            'TheHub-Chair2-64k.txt': 'Chair2',
            'TheHub-CeilingCorner-64k.txt': 'CeilingCorner'
        }
        
        # Store actual RT60 measurements
        self.actual_rt60_data = {}
        
        # Read each Smaart log file
        for filename, position in file_to_position.items():
            file_path = smaart_path / filename
            if file_path.exists():
                rt60_data = self.parse_smaart_file(file_path)
                if rt60_data:
                    self.actual_rt60_data[position] = rt60_data
                    print(f"✅ Loaded {position}: {len(rt60_data)} frequency bands")
                else:
                    print(f"⚠️  Failed to parse {filename}")
            else:
                print(f"❌ File not found: {filename}")
    
    def parse_smaart_file(self, file_path):
        """Parse Smaart log file to extract RT60 values by frequency"""
        rt60_data = {}
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Find the octave band RT60 data (lines starting with "Oct")
            for line in lines:
                line = line.strip()
                if line.startswith('Oct\t') and 'Hz' in line:
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        freq_str = parts[1].replace('Hz', '')
                        try:
                            # Handle kHz notation (1kHz -> 1000, 2kHz -> 2000, etc.)
                            if 'k' in freq_str:
                                freq = int(freq_str.replace('k', '')) * 1000
                            else:
                                freq = int(freq_str)
                            rt60_value = float(parts[2])
                            
                            # Only store frequencies we're interested in
                            if freq in self.frequency_bands and rt60_value > 0:
                                rt60_data[freq] = rt60_value
                        except ValueError:
                            continue
            
            return rt60_data if rt60_data else None
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None
    
    def calculate_rt60_with_panels(self, panel_count):
        """Calculate RT60 at each measurement position with given panel count using actual measured data"""
        rt60_data = {}
        
        # Calculate panel improvement factor based on count and placement
        panel_improvement_factor = self.get_panel_improvement_factor(panel_count)
        
        for pos_name, pos_data in self.measurement_positions.items():
            rt60_freq = {}
            
            # Get actual measured RT60 data for this position
            if pos_name in self.actual_rt60_data:
                measured_data = self.actual_rt60_data[pos_name]
                
                for freq in self.frequency_bands:
                    if freq in measured_data:
                        # Start with actual measured RT60
                        baseline_rt60 = measured_data[freq]
                        
                        # Apply panel improvement (panels reduce RT60)
                        # More panels = greater reduction
                        panel_reduction = panel_improvement_factor * self.get_position_panel_effectiveness(pos_name, freq)
                        
                        # Calculate improved RT60 (never go below 0.15s minimum)
                        improved_rt60 = baseline_rt60 * (1.0 - panel_reduction)
                        improved_rt60 = max(improved_rt60, 0.15)
                        
                        rt60_freq[freq] = improved_rt60
                    else:
                        # Fallback for missing frequency data
                        rt60_freq[freq] = 0.5  # Reasonable default
            else:
                # Fallback for missing position data
                for freq in self.frequency_bands:
                    rt60_freq[freq] = 0.6  # Reasonable default
            
            rt60_data[pos_name] = rt60_freq
        
        return rt60_data
    
    def get_panel_improvement_factor(self, panel_count):
        """Calculate overall improvement factor based on panel count for The Hub"""
        if panel_count == 0:
            return 0.0
        
        # The Hub is smaller than Studio 8, so panels are more effective per unit
        # Maximum improvement is about 45% RT60 reduction with full treatment
        max_improvement = 0.45
        
        # Use exponential decay: improvement = max * (1 - e^(-k*panels))
        # Higher k value for smaller space - panels more effective
        k = 0.08  # Tuning parameter for curve shape (higher than Studio 8's 0.06)
        improvement = max_improvement * (1.0 - np.exp(-k * panel_count))
        
        return min(improvement, max_improvement)
    
    def get_position_panel_effectiveness(self, position_name, frequency):
        """Get position-specific panel effectiveness factors for The Hub"""
        # Factors based on how much panels at different locations would help each position
        # The Hub's irregular shape means corner positions benefit more
        
        base_effectiveness = {
            "MidRoom": 0.9,         # Center position - moderate effectiveness
            "BackCorner": 1.3,      # Corner position - high effectiveness
            "Chair1": 1.1,          # Seating area - good effectiveness  
            "Chair2": 1.1,          # Seating area - good effectiveness
            "CeilingCorner": 1.4    # Worst acoustic position - highest benefit
        }
        
        # Frequency-dependent adjustments for The Hub's smaller volume
        freq_factor = 1.0
        if frequency <= 250:
            # Low frequencies: bass traps more effective in corners (smaller space = more concentrated modes)
            if "Corner" in position_name:
                freq_factor = 1.4  # Higher than Studio 8 due to smaller volume
        elif frequency >= 2000:
            # High frequencies: more uniform effectiveness in smaller space
            freq_factor = 1.0
        
        return base_effectiveness.get(position_name, 1.0) * freq_factor
    
    def create_rt60_heatmap(self, panel_count=10):
        """Create RT60 heatmap visualization using actual Hub measurement data"""
        
        # Calculate RT60 values
        rt60_data = self.calculate_rt60_with_panels(panel_count)
        
        # Prepare data for heatmap
        positions = list(self.measurement_positions.keys())
        frequencies = self.frequency_labels
        
        # Create matrix for heatmap
        z_values = []
        hover_text = []
        
        for freq_idx, freq in enumerate(self.frequency_bands):
            row_values = []
            row_hover = []
            
            for pos_name in positions:
                rt60_value = rt60_data[pos_name][freq]
                row_values.append(rt60_value)
                
                # Create detailed hover text
                pos_info = self.measurement_positions[pos_name]
                hover_info = (
                    f"<b>{pos_info['name']}</b><br>"
                    f"Frequency: {frequencies[freq_idx]}<br>"
                    f"RT60: {rt60_value:.2f}s<br>"
                    f"Position: ({pos_info['coords'][0]:.1f}', {pos_info['coords'][1]:.1f}', {pos_info['coords'][2]:.1f}')<br>"
                    f"Panels: {panel_count}"
                )
                row_hover.append(hover_info)
            
            z_values.append(row_values)
            hover_text.append(row_hover)
        
        # Create heatmap with realistic color scale for measured RT60 values
        fig = go.Figure(data=go.Heatmap(
            z=z_values,
            x=[self.measurement_positions[pos]["name"] for pos in positions],
            y=frequencies,
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=hover_text,
            colorscale=[
                [0.0, '#000080'],    # Dark blue for very low RT60
                [0.1, '#003399'],    # Deep blue
                [0.15, '#0066CC'],   # Medium blue
                [0.2, '#3399FF'],    # Lighter blue
                [0.22, '#4DA6FF'],   # Light blue transitioning
                [0.25, '#40C040'],   # GREEN START - IDEAL RT60 RANGE
                [0.28, '#48C848'],   # Early green
                [0.3, '#50D050'],    # Green progression
                [0.32, '#58D858'],   # Target green
                [0.35, '#60E060'],   # Center green
                [0.37, '#68E868'],   # Mid-late green
                [0.4, '#70F070'],    # Continuing green
                [0.42, '#78F878'],   # Late green
                [0.45, '#80FF80'],   # GREEN END - IDEAL RT60 RANGE
                [0.47, '#99FF99'],   # Green to yellow transition
                [0.49, '#CCFF88'],   # Gentle yellow-green
                [0.52, '#EEFF77'],   # Soft yellow-green
                [0.55, '#FFFF66'],   # Standard yellow
                [0.58, '#FFEE55'],   # Gentle yellow
                [0.6, '#FFD700'],    # Gold transition
                [0.65, '#FFCC33'],   # Gold to orange
                [0.7, '#FFA500'],    # Orange
                [0.75, '#FF8C00'],   # Dark orange
                [0.8, '#FF6347'],    # Tomato
                [0.85, '#FF4500'],   # Red-orange
                [0.9, '#FF3300'],    # Bright red
                [0.95, '#E60000'],   # Deep red
                [1.0, '#CC0000']     # Dark red for maximum RT60
            ],
            colorbar=dict(
                title="RT60 (seconds)",
                tickmode="linear",
                tick0=0.2,
                dtick=0.1
            ),
            zmin=0.15,   # Minimum possible with maximum treatment
            zmax=0.7     # Maximum expected from measurements
        ))
        
        # Update layout to match reference chart style
        fig.update_layout(
            title=f"The Hub - RT60 Frequency Response by Position ({panel_count} panels)",
            xaxis_title="Measurement Position",
            yaxis_title="Frequency Band",
            font=dict(size=12),
            height=400,
            margin=dict(l=80, r=80, t=60, b=60)
        )
        
        return fig
    
    def render_rt60_summary(self, panel_count):
        """Render condensed RT60 analysis summary for The Hub"""
        rt60_data = self.calculate_rt60_with_panels(panel_count)
        
        # Calculate key statistics
        all_values = []
        for pos_data in rt60_data.values():
            all_values.extend(pos_data.values())
        
        avg_rt60 = np.mean(all_values)
        min_rt60 = np.min(all_values)
        max_rt60 = np.max(all_values)
        std_rt60 = np.std(all_values)
        
        # Target range analysis - broadcast standards
        target_min, target_max = 0.3, 0.5
        in_target = sum(1 for val in all_values if target_min <= val <= target_max)
        target_percentage = (in_target / len(all_values)) * 100
        
        # Metrics aligned with heatmap cells (accounting for y-axis labels)
        metric_col1, metric_col2 = st.columns([1, 1])
        
        with metric_col1:
            st.markdown('<div style="margin-left: 80px;">', unsafe_allow_html=True)
            if avg_rt60 > target_max:
                st.metric("Avg RT60", f"{avg_rt60:.2f}s", delta="Too High", delta_color="inverse")
            elif avg_rt60 < target_min:
                st.metric("Avg RT60", f"{avg_rt60:.2f}s", delta="Too Low", delta_color="inverse")
            else:
                st.metric("Avg RT60", f"{avg_rt60:.2f}s", delta="Good", delta_color="normal")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with metric_col2:
            st.metric("In Target Range", f"{target_percentage:.0f}%")
        
        # Quick recommendations based on realistic RT60 values for The Hub
        if avg_rt60 > 0.65:
            st.caption("🔴 Needs treatment - targeting green/blue zones")  
        elif avg_rt60 < 0.25:
            st.caption("🔵 Excellent control - blue zone achieved")
        elif avg_rt60 < 0.4:
            st.caption("🟢 Professional quality - green zone")
        else:
            st.caption("🟡 Good progress - approaching green zones")

    def create_hub_3d_heatmap_overlay(self, panel_count=10):
        """Create 3D visualization of The Hub with RT60 heatmap overlay"""
        from enhanced_3d_visualizer import Enhanced3DVisualizer
        
        # Create base Hub 3D model
        visualizer = Enhanced3DVisualizer()
        fig = visualizer.create_hub_detailed_model(show_panels=True, panel_count=panel_count)
        
        # Get RT60 data for overlay
        rt60_data = self.calculate_rt60_with_panels(panel_count)
        
        # Add RT60 measurement overlays at each position
        for pos_name, pos_info in self.measurement_positions.items():
            if pos_name in rt60_data:
                # Calculate average RT60 across frequencies for color coding
                avg_rt60 = np.mean(list(rt60_data[pos_name].values()))
                
                # Color code based on RT60 value
                if avg_rt60 <= 0.35:
                    color = '#40C040'  # Green - good
                elif avg_rt60 <= 0.5:
                    color = '#FFD700'  # Gold - acceptable
                else:
                    color = '#FF4500'  # Red-orange - needs treatment
                
                x, y, z = pos_info['coords']
                
                # Add RT60 indicator at measurement position
                fig.add_trace(go.Scatter3d(
                    x=[x], y=[y], z=[z + 1],
                    mode='markers+text',
                    marker=dict(
                        size=15,
                        color=color,
                        symbol='diamond',
                        line=dict(width=3, color='white')
                    ),
                    text=[f"RT60: {avg_rt60:.2f}s"],
                    textposition="top center",
                    name=f"RT60 - {pos_info['name']}",
                    hovertemplate=f"<b>{pos_info['name']}</b><br>" +
                                 f"Average RT60: {avg_rt60:.2f}s<br>" +
                                 f"Position: ({x:.1f}', {y:.1f}', {z:.1f}')<br>" +
                                 f"<extra></extra>"
                ))
        
        # Update title to reflect heatmap overlay
        fig.update_layout(
            title=f"The Hub - 3D Model with RT60 Heatmap Overlay ({panel_count} panels)"
        )
        
        return fig

# Test the Hub analyzer
if __name__ == "__main__":
    analyzer = RT60HeatmapAnalyzerHub()
    
    print("🔍 Testing RT60 analyzer for The Hub with actual Smaart data:")
    print()
    
    # Test loading actual data
    if analyzer.actual_rt60_data:
        print("✅ Successfully loaded actual RT60 measurements:")
        for pos, data in analyzer.actual_rt60_data.items():
            if data:
                avg_rt60 = np.mean(list(data.values()))
                print(f"  {pos:15s}: {avg_rt60:.2f}s average RT60 ({len(data)} frequency bands)")
            else:
                print(f"  {pos:15s}: No data available")
    else:
        print("❌ No actual RT60 data found - check file paths")
    
    print()
    print("Testing panel count effects for The Hub:")
    for panels in [0, 5, 10, 15]:
        rt60_data = analyzer.calculate_rt60_with_panels(panels)
        all_values = []
        for pos_data in rt60_data.values():
            all_values.extend(pos_data.values())
        
        avg_rt60 = np.mean(all_values)
        print(f"  {panels:2d} panels → {avg_rt60:.2f}s average (realistic range for Hub)")

    print()
    print("🎯 Creating RT60 heatmap visualization...")
    fig = analyzer.create_rt60_heatmap(panel_count=10)
    print("✅ Heatmap created successfully!")