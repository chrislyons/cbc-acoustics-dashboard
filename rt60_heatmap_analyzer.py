#!/usr/bin/env python3
"""
RT60 Heatmap Analyzer - Dynamic RT60 visualization showing acoustic changes with panel placement
Inspired by the reference RT60 heatmap showing position-based frequency response
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st

class RT60HeatmapAnalyzer:
    def __init__(self):
        # Studio 8 dimensions
        self.room_width_EW = 23.375  # East-West (short walls)
        self.room_length_NS = 27.42  # North-South (long walls)
        self.room_height = 14.0
        
        # Frequency bands for analysis (matching reference chart)
        self.frequency_bands = [125, 250, 500, 1000, 2000, 4000, 8000]
        self.frequency_labels = ['125Hz', '250Hz', '500Hz', '1kHz', '2kHz', '4kHz', '8kHz']
        
        # Measurement positions (matching Enhanced3DVisualizer)
        self.measurement_positions = {
            "HostA": {"coords": [self.room_width_EW/2 + 4, (self.room_length_NS/2) - 7, 5.5], "name": "Host A"},
            "HostC": {"coords": [self.room_width_EW/2 - 4, (self.room_length_NS/2) - 7, 5.5], "name": "Host C"}, 
            "Ceiling": {"coords": [self.room_width_EW/2, self.room_length_NS/2 + 3, 5.5], "name": "Ceiling"},
            "SECorner": {"coords": [19.5, 2.5, 7.5], "name": "SE Corner"},
            "MidRoom": {"coords": [self.room_width_EW/2, (self.room_length_NS/2) + 8, 5.5], "name": "Mid Room"},
            "NECorner": {"coords": [20.5, 24.9, 11.5], "name": "NE Corner"},
            "SWCorner": {"coords": [5.2, 3.9, 5.5], "name": "SW Corner"},
            "NWCorner": {"coords": [5.2, 23.5, 5.5], "name": "NW Corner"}
        }
        
        # Load actual RT60 measurements from Smaart logs
        self.load_smaart_rt60_data()
    
    def load_smaart_rt60_data(self):
        """Load actual RT60 measurements from Smaart log files"""
        import os
        from pathlib import Path
        
        # Path to Smaart logs
        smaart_path = Path('data/raw/250715-smaartLogs/Std8')
        
        # Mapping from file names to our position names
        file_to_position = {
            'Std8-HostA-128k-Sweep.txt': 'HostA',
            'Std8-HostC-128k-Sweep.txt': 'HostC', 
            'Std8-Ceiling-128k-Sweep.txt': 'Ceiling',
            'Std8-SECorner-128k-Sweep.txt': 'SECorner',
            'Std8-MidRoom-128k-Sweep.txt': 'MidRoom',
            'Std8-NECorner-High-128k-Sweep.txt': 'NECorner',
            'Std8-SWCorner-128k-Sweep.txt': 'SWCorner'
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
        
        # Add NWCorner with estimated values (no measurement file found)
        if 'SWCorner' in self.actual_rt60_data:
            self.actual_rt60_data['NWCorner'] = self.actual_rt60_data['SWCorner'].copy()
    
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
    
    def calculate_baseline_absorption(self):
        """Calculate baseline room absorption without treatment panels"""
        # Surface areas
        floor_area = self.room_width_EW * self.room_length_NS
        ceiling_area = floor_area
        wall_area_NS = 2 * self.room_length_NS * self.room_height  # North/South walls
        wall_area_EW = 2 * self.room_width_EW * self.room_height   # East/West walls
        total_wall_area = wall_area_NS + wall_area_EW
        
        # Baseline absorption coefficients for untreated office space
        # Values from foundational_acoustics_reference.md - typical office materials
        baseline_absorption = {
            125: {'floor': 0.02, 'ceiling': 0.14, 'walls': 0.03},   # Concrete/drywall
            250: {'floor': 0.02, 'ceiling': 0.10, 'walls': 0.04},
            500: {'floor': 0.03, 'ceiling': 0.06, 'walls': 0.05},
            1000: {'floor': 0.04, 'ceiling': 0.04, 'walls': 0.06},
            2000: {'floor': 0.04, 'ceiling': 0.04, 'walls': 0.08},
            4000: {'floor': 0.05, 'ceiling': 0.03, 'walls': 0.10},
            8000: {'floor': 0.05, 'ceiling': 0.03, 'walls': 0.12}
        }
        
        # Calculate total baseline absorption by frequency
        self.baseline_absorption = {}
        for freq in self.frequency_bands:
            total_absorption = (
                floor_area * baseline_absorption[freq]['floor'] +
                ceiling_area * baseline_absorption[freq]['ceiling'] +
                total_wall_area * baseline_absorption[freq]['walls']
            )
            self.baseline_absorption[freq] = total_absorption
    
    def calculate_rt60_with_panels(self, panel_count):
        """Calculate RT60 at each measurement position with given panel count"""
        rt60_data = {}
        
        # Get panel absorption based on placement strategy from Enhanced3DVisualizer
        panel_absorption = self.get_panel_absorption_by_count(panel_count)
        
        for pos_name, pos_data in self.measurement_positions.items():
            rt60_freq = {}
            
            for freq in self.frequency_bands:
                # Total absorption = baseline + panels
                total_absorption = self.baseline_absorption[freq] + panel_absorption[freq]
                
                # Apply position-specific adjustments based on room acoustics
                position_factor = self.get_position_factor(pos_name, freq)
                adjusted_absorption = total_absorption * position_factor
                
                # Sabine equation: RT60 = 0.161 * V / Sa
                rt60 = 0.161 * self.room_volume / max(adjusted_absorption, 0.1)  # Avoid division by zero
                
                # Apply air absorption for higher frequencies (per foundational reference)
                if freq >= 2000:
                    air_absorption = self.get_air_absorption(freq, self.room_volume)
                    rt60 = rt60 / (1 + air_absorption)
                
                rt60_freq[freq] = rt60
            
            rt60_data[pos_name] = rt60_freq
        
        return rt60_data
    
    def get_panel_absorption_by_count(self, panel_count):
        """Calculate total panel absorption based on placement strategy"""
        absorption_by_freq = {freq: 0.0 for freq in self.frequency_bands}
        
        if panel_count == 0:
            return absorption_by_freq
        
        # Panel placement strategy from Enhanced3DVisualizer
        # Priority 1: Corner bass traps (5.5") - up to 4 panels
        corner_traps = min(4, panel_count)
        for freq in self.frequency_bands:
            absorption_by_freq[freq] += corner_traps * self.panel_area * self.panel_absorption_5_5_inch[freq]
        
        remaining_panels = panel_count - corner_traps
        
        # Priority 2: High midpoint panels (5.5") - up to 3 panels
        if remaining_panels > 0:
            midpoint_panels = min(3, remaining_panels)
            for freq in self.frequency_bands:
                absorption_by_freq[freq] += midpoint_panels * self.panel_area * self.panel_absorption_5_5_inch[freq]
            remaining_panels -= midpoint_panels
        
        # Priority 3: Ceiling center panels (5.5") - up to 9 panels
        if remaining_panels > 0:
            ceiling_panels = min(9, remaining_panels)
            for freq in self.frequency_bands:
                absorption_by_freq[freq] += ceiling_panels * self.panel_area * self.panel_absorption_5_5_inch[freq]
            remaining_panels -= ceiling_panels
        
        # Priority 4: North wall panels (3") - up to 4 panels
        if remaining_panels > 0:
            wall_panels = min(4, remaining_panels)
            for freq in self.frequency_bands:
                absorption_by_freq[freq] += wall_panels * self.panel_area * self.panel_absorption_3_inch[freq]
            remaining_panels -= wall_panels
        
        # Priority 5: Grid clouds (3") - remaining panels
        if remaining_panels > 0:
            cloud_panels = remaining_panels
            for freq in self.frequency_bands:
                absorption_by_freq[freq] += cloud_panels * self.panel_area * self.panel_absorption_3_inch[freq]
        
        return absorption_by_freq
    
    def get_position_factor(self, position_name, frequency):
        """Get position-specific acoustic adjustment factors"""
        # Factors based on Studio 8 modal analysis and measurement data
        # Corner positions experience more modal effects, center positions more direct sound
        
        base_factors = {
            "HostA": 1.0,      # Reference position
            "HostC": 1.02,     # Slightly more reverberant due to asymmetry
            "Ceiling": 0.92,   # Higher position, less boundary effects
            "SECorner": 1.15,  # Corner loading, more modal interaction
            "MidRoom": 0.88,   # Open space, less boundary reflection
            "NECorner": 1.18,  # Worst corner for modals
            "SWCorner": 1.12,  # Corner effects
            "NWCorner": 1.08   # Near hallway opening, slightly better
        }
        
        # Frequency-dependent adjustments
        if frequency <= 250:
            # Low frequencies: corner effects more pronounced
            if "Corner" in position_name:
                return base_factors[position_name] * 1.25
        elif frequency >= 2000:
            # High frequencies: more localized, less position variation
            return base_factors[position_name] * 0.95
        
        return base_factors[position_name]
    
    def get_air_absorption(self, frequency, volume):
        """Calculate air absorption for high frequencies"""
        # Air absorption coefficient (per foundational_acoustics_reference.md)
        if frequency == 2000:
            return 0.0033 * volume / 1000  # 0.33% per 1000 cubic feet
        elif frequency == 4000:
            return 0.0102 * volume / 1000  # 1.02% per 1000 cubic feet
        elif frequency == 8000:
            return 0.0324 * volume / 1000  # 3.24% per 1000 cubic feet
        return 0.0
    
    def create_rt60_heatmap(self, panel_count=25):
        """Create RT60 heatmap visualization inspired by reference chart"""
        
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
        
        # Create heatmap with improved color scale weighting
        fig = go.Figure(data=go.Heatmap(
            z=z_values,
            x=[self.measurement_positions[pos]["name"] for pos in positions],
            y=frequencies,
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=hover_text,
            colorscale=[
                [0.0, '#00008B'],    # Dark blue for excellent RT60 (≤2s) - BEST
                [0.1, '#00BFFF'],    # Light blue for very good RT60 (2-2.5s) - NARROW BLUE RANGE
                [0.2, '#32CD32'],    # Green for good RT60 (2.5-3.5s)
                [0.35, '#90EE90'],   # Light green for acceptable RT60 (3.5-4.5s)
                [0.5, '#FFD700'],    # Gold for moderate RT60 (4.5-5.5s)
                [0.65, '#FFA500'],   # Orange for elevated RT60 (5.5-6.5s)
                [0.75, '#FF6347'],   # Tomato for high RT60 (6.5-7.5s)
                [0.85, '#FF4500'],   # Red-orange for very high RT60 (7.5-9s)
                [0.95, '#DC143C'],   # Crimson for extremely high RT60 (9-11s)
                [1.0, '#8B0000']     # Dark red for maximum RT60 (≥11s) - WORST
            ],
            colorbar=dict(
                title="RT60 (seconds)",
                tickmode="linear",
                tick0=2.0,
                dtick=2.0
            ),
            zmin=1.5,   # Minimum expected RT60 with maximum treatment
            zmax=13.0   # Maximum expected RT60 without treatment
        ))
        
        # Update layout to match reference chart style
        fig.update_layout(
            title=f"Studio 8 - RT60 Frequency Response by Position ({panel_count} panels)",
            xaxis_title="Measurement Position",
            yaxis_title="Frequency Band",
            font=dict(size=12),
            height=400,
            margin=dict(l=80, r=80, t=60, b=60)
        )
        
        return fig
    
    def create_rt60_delta_heatmap(self, current_panels, baseline_panels=0):
        """Create delta heatmap showing RT60 changes from baseline"""
        
        current_rt60 = self.calculate_rt60_with_panels(current_panels)
        baseline_rt60 = self.calculate_rt60_with_panels(baseline_panels)
        
        positions = list(self.measurement_positions.keys())
        frequencies = self.frequency_labels
        
        # Calculate deltas
        z_values = []
        hover_text = []
        
        for freq_idx, freq in enumerate(self.frequency_bands):
            row_values = []
            row_hover = []
            
            for pos_name in positions:
                current_value = current_rt60[pos_name][freq]
                baseline_value = baseline_rt60[pos_name][freq]
                delta = current_value - baseline_value
                row_values.append(delta)
                
                pos_info = self.measurement_positions[pos_name]
                hover_info = (
                    f"<b>{pos_info['name']}</b><br>"
                    f"Frequency: {frequencies[freq_idx]}<br>"
                    f"RT60 Change: {delta:+.2f}s<br>"
                    f"Current: {current_value:.2f}s<br>"
                    f"Baseline: {baseline_value:.2f}s<br>"
                    f"Panels: {current_panels} → {current_panels}"
                )
                row_hover.append(hover_info)
            
            z_values.append(row_values)
            hover_text.append(row_hover)
        
        # Create delta heatmap
        fig = go.Figure(data=go.Heatmap(
            z=z_values,
            x=[self.measurement_positions[pos]["name"] for pos in positions],
            y=frequencies,
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=hover_text,
            colorscale='RdBu_r',  # Red for increases, Blue for decreases
            colorbar=dict(
                title="RT60 Change (s)"
            ),
            zmid=0  # Center the colorscale at zero
        ))
        
        fig.update_layout(
            title=f"Studio 8 - RT60 Change from Baseline ({current_panels} vs {baseline_panels} panels)",
            xaxis_title="Measurement Position", 
            yaxis_title="Frequency Band",
            font=dict(size=12),
            height=400,
            margin=dict(l=80, r=80, t=60, b=60)
        )
        
        return fig
    
    def render_rt60_heatmap_interface(self):
        """Streamlit interface for RT60 heatmap analysis"""
        
        st.subheader("Dynamic RT60 Heatmap Analysis")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("**Controls**")
            
            # Panel count slider
            panel_count = st.slider(
                "Treatment Panels", 
                min_value=0, 
                max_value=40, 
                value=25,
                help="Number of acoustic treatment panels to model"
            )
            
            # Visualization options
            show_delta = st.checkbox(
                "Show Delta from Baseline", 
                help="Display RT60 changes relative to untreated room"
            )
            
            if show_delta:
                baseline_panels = st.slider(
                    "Baseline Panel Count", 
                    min_value=0, 
                    max_value=panel_count, 
                    value=0
                )
        
        with col2:
            # Generate and display heatmap
            if show_delta:
                fig = self.create_rt60_delta_heatmap(panel_count, baseline_panels)
            else:
                fig = self.create_rt60_heatmap(panel_count)
            
            st.plotly_chart(fig, use_container_width=True)
        
        # RT60 targets and analysis
        with st.expander("📊 RT60 Analysis & Targets"):
            self.render_rt60_analysis(panel_count)
    
    def render_rt60_analysis(self, panel_count):
        """Render RT60 analysis summary"""
        
        rt60_data = self.calculate_rt60_with_panels(panel_count)
        
        # Calculate statistics
        all_values = []
        for pos_data in rt60_data.values():
            all_values.extend(pos_data.values())
        
        avg_rt60 = np.mean(all_values)
        min_rt60 = np.min(all_values)
        max_rt60 = np.max(all_values)
        std_rt60 = np.std(all_values)
        
        # Target range analysis - adjusted for actual Studio 8 conditions
        # Professional broadcast target: 2-4s (more realistic for untreated office conversion)
        target_min, target_max = 2.0, 4.0
        in_target = sum(1 for val in all_values if target_min <= val <= target_max)
        target_percentage = (in_target / len(all_values)) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Average RT60", f"{avg_rt60:.2f}s")
        with col2:
            st.metric("RT60 Range", f"{min_rt60:.2f} - {max_rt60:.2f}s")
        with col3:
            st.metric("Std Deviation", f"{std_rt60:.2f}s")
        with col4:
            st.metric("In Target Range", f"{target_percentage:.0f}%")
        
        # Recommendations  
        if avg_rt60 > 6.5:
            st.error("🔴 **RT60 too high** - Room needs significant treatment (red zones)")
        elif avg_rt60 < 2.5:
            st.info("🔵 **Excellent RT60** - Optimal acoustic control achieved (blue zone)")
        elif avg_rt60 < 3.5:
            st.success("🟢 **Good RT60** - Professional broadcast quality (green zone)")
        elif avg_rt60 < 5.5:
            st.warning("🟡 **Moderate RT60** - More treatment recommended (gold zone)")
        else:
            st.warning("🟠 **Elevated RT60** - Significant treatment needed (orange zone)")
        
        if std_rt60 > 1.0:
            st.info("💡 **High variation** - Consider redistributing panels for more even coverage")

# Example usage for testing
if __name__ == "__main__":
    analyzer = RT60HeatmapAnalyzer()
    
    # Test RT60 calculation
    rt60_0_panels = analyzer.calculate_rt60_with_panels(0)
    rt60_25_panels = analyzer.calculate_rt60_with_panels(25)
    
    print("RT60 without panels (HostA, 1kHz):", rt60_0_panels["HostA"][1000])
    print("RT60 with 25 panels (HostA, 1kHz):", rt60_25_panels["HostA"][1000])