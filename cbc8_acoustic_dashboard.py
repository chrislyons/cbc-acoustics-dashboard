#!/usr/bin/env python3
"""
Fixed Interactive Web Dashboard for CBC Studio 8 & Hub Acoustic Analysis
Removed problematic CSS transitions that may cause scroll crashes
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from pathlib import Path
import re
from datetime import datetime

# Import our specialized components with error handling
try:
    from enhanced_3d_visualizer import Enhanced3DVisualizer
    from frequency_response_explorer import FrequencyResponseExplorer
    from treatment_simulator import TreatmentSimulator
    from rt60_heatmap_analyzer_fixed import RT60HeatmapAnalyzer
    from data_explorer import render_data_explorer
    COMPONENTS_LOADED = True
    COMPONENT_ERROR = None
except ImportError as e:
    COMPONENTS_LOADED = False
    COMPONENT_ERROR = f"⚠️ Component import error: {e}"

# Simplified CSS without problematic transitions and transforms
DASHBOARD_CSS = """
<style>
    /* Import Inter font from Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global font family override */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    
    /* Simplified styling without animations */
    :root {
        --bg-primary: #ffffff;
        --bg-secondary: #f8f9fa;
        --text-primary: #333333;
        --text-secondary: #666666;
        --border-color: #dee2e6;
        --accent-blue: #007bff;
        --accent-red: #e74c3c;
        --accent-green: #27ae60;
        --accent-orange: #f39c12;
    }
    
    /* Override dark theme to force light mode */
    [data-theme="dark"] {
        --bg-primary: #ffffff !important;
        --bg-secondary: #f8f9fa !important;
        --text-primary: #333333 !important;
        --text-secondary: #666666 !important;
        --border-color: #dee2e6 !important;
        --accent-blue: #007bff !important;
        --accent-red: #e74c3c !important;
        --accent-green: #27ae60 !important;
        --accent-orange: #f39c12 !important;
        background-color: #ffffff !important;
        color: #333333 !important;
    }
    
    .main-header {
        background: linear-gradient(90deg, #e74c3c, #ffffff, #e74c3c);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: var(--bg-secondary);
        color: var(--text-primary);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid var(--accent-blue);
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        /* REMOVED: transition and transform that could cause scroll issues */
    }
    
    .problem-highlight {
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.15), rgba(255, 193, 7, 0.08));
        border: 2px solid var(--accent-orange);
        color: var(--text-primary);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        box-shadow: 0 2px 10px rgba(255, 193, 7, 0.1);
    }
    
    .solution-highlight {
        background: linear-gradient(135deg, rgba(74, 185, 255, 0.15), rgba(74, 185, 255, 0.08));
        border: 2px solid var(--accent-blue);
        color: var(--text-primary);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        box-shadow: 0 2px 10px rgba(74, 185, 255, 0.1);
    }
    
    .critical-metric {
        color: var(--accent-red);
        font-weight: bold;
    }
    
    .good-metric {
        color: var(--accent-green);
        font-weight: bold;
    }
    
    .warning-metric {
        color: var(--accent-orange);
        font-weight: bold;
    }
    
    /* Enhanced text readability */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
        opacity: 1;
    }
    
    p, li, span, div, strong, em {
        color: var(--text-primary);
        opacity: 1;
    }
    
    /* Professional metric styling */
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0.5rem 0;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    .metric-label {
        font-size: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        opacity: 0.8;
    }
    
    .metric-subtitle {
        font-size: 0.9rem;
        opacity: 0.7;
        margin-top: 0.5rem;
    }
    
    /* Sidebar styling with navy blue tint - comprehensive targeting */
    .css-1d391kg, .css-1d391kg .css-1aumxhk, section[data-testid="stSidebar"] {
        background-color: #d6dce5 !important; /* Light grey-navy mix */
    }
    
    .css-1d391kg .stMarkdown, .css-1d391kg .stSelectbox, .css-1d391kg .stHeader {
        background-color: transparent !important;
    }
    
    /* Force sidebar background with higher specificity */
    .stApp > .main .css-1d391kg {
        background-color: #d6dce5 !important; /* Light grey-navy mix */
    }
    
    /* Alternative targeting for different Streamlit versions */
    section[data-testid="stSidebar"] > div:first-child {
        background-color: #d6dce5 !important;
    }
    
    /* Dark mode */
    [data-theme="dark"] .css-1d391kg, 
    [data-theme="dark"] section[data-testid="stSidebar"] {
        background-color: #1a1f2e !important; /* Dark grey-navy mix */
    }
</style>
"""

class AcousticDashboard:
    def __init__(self):
        self.base_path = Path('.')
        self.data_cache = {}
        
        # Initialize specialized components with error handling
        try:
            if COMPONENTS_LOADED:
                self.visualizer_3d = Enhanced3DVisualizer()
                self.freq_explorer = FrequencyResponseExplorer()
                self.treatment_sim = TreatmentSimulator()
                self.rt60_analyzer = RT60HeatmapAnalyzer()
            else:
                self.visualizer_3d = None
                self.freq_explorer = None
                self.treatment_sim = None
                self.rt60_analyzer = None
        except Exception as e:
            st.error(f"⚠️ Component initialization error: {e}")
            self.visualizer_3d = None
            self.freq_explorer = None  
            self.treatment_sim = None
            self.rt60_analyzer = None
        
    def load_csv_data(self, filename_pattern):
        """Load CSV data matching pattern"""
        try:
            matching_files = list(self.base_path.glob(f"*{filename_pattern}*.csv"))
            if matching_files:
                return pd.read_csv(matching_files[0])
            return None
        except Exception as e:
            st.error(f"Error loading {filename_pattern}: {e}")
            return None
    
    def get_space_data_files(self, space):
        """Get space-specific data file paths"""
        space_id = "Studio8" if space == "Studio 8" else "TheHub"
        
        # Map of data types to file patterns
        data_files = {
            'frequency_response': f'data/generated/*{space_id}-Complete_Frequency_Response.csv',
            'treatment_priority': f'data/generated/*{space_id}-Treatment_Priority_Matrix.csv',
            'evidence_degradation': f'data/generated/*{space_id}-Evidence_Degradation_Analysis.csv',
            'modal_stack': f'data/generated/*{space_id}-Modal_Stack_Analysis.csv',
            'drape_compensation': f'data/generated/*{space_id}-Drape_Compensation_Evidence.csv'
        }
        
        return data_files
    
    def load_space_data(self, space, data_type):
        """Load specific data type for a given space"""
        try:
            data_files = self.get_space_data_files(space)
            if data_type in data_files:
                matching_files = list(self.base_path.glob(data_files[data_type]))
                if matching_files:
                    return pd.read_csv(matching_files[0])
            return None
        except Exception as e:
            st.error(f"Error loading {data_type} data for {space}: {e}")
            return None
    
    def render_dashboard(self):
        """Main dashboard rendering function"""
        
        # Header
        st.markdown("""
        <div class="main-header">
            <h1>CBC Sports 8th Floor Acoustics Dashboard</h1>
            <p>Interactive visualization of Studio 8 & Hub acoustic treatment analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sidebar controls
        st.sidebar.header("🎛️ Dashboard Controls")
        
        # Get URL query parameters for page persistence
        query_params = st.query_params
        
        # Initialize session state for persistence
        if "selected_space" not in st.session_state:
            st.session_state.selected_space = query_params.get("space", "Studio 8")
        if "viz_type" not in st.session_state:
            st.session_state.viz_type = query_params.get("page", "Summary")
        
        # Space selection with persistence
        selected_space = st.sidebar.selectbox(
            "Broadcast Space",
            ["Studio 8", "The Hub"],
            index=["Studio 8", "The Hub"].index(st.session_state.selected_space) if st.session_state.selected_space in ["Studio 8", "The Hub"] else 0,
            help="Choose which broadcast space to analyze",
            key="space_selector"
        )
        # Add delay for smoothness
        import time
        time.sleep(0.05)
        
        # Update session state and URL when space changes
        if selected_space != st.session_state.selected_space:
            st.session_state.selected_space = selected_space
            st.query_params["space"] = selected_space
            # Clear any cached data when space changes to force refresh
            if hasattr(st.session_state, 'cached_3d_fig'):
                st.session_state.cached_3d_fig = None
            if hasattr(st.session_state, 'cached_rt60_fig'):
                st.session_state.cached_rt60_fig = None
            # Reset panel count to space-appropriate default
            default_count = 10 if selected_space == "The Hub" else 25
            st.session_state.panel_count = default_count
            # Force rerun to refresh all components
            st.rerun()
        
        # Visualization type with persistence
        page_options = ["Summary", "Data Explorer", "3D Room Model", "Frequency Analysis", "Treatment Simulator", "Complete Analysis"]
        viz_type = st.sidebar.selectbox(
            "Viewer",
            page_options,
            index=page_options.index(st.session_state.viz_type) if st.session_state.viz_type in page_options else 0,
            help="Select the type of analysis to display",
            key="page_selector"
        )
        # Add delay for smoothness
        time.sleep(0.05)
        
        # Update session state and URL when page changes
        if viz_type != st.session_state.viz_type:
            st.session_state.viz_type = viz_type
            st.query_params["page"] = viz_type
        
        # Camera presets for 3D Room Model
        selected_preset = None
        if viz_type == "3D Room Model":
            st.sidebar.markdown("---")
            st.sidebar.markdown("**Camera Presets:**")
            
            camera_presets = {
                "Default": {"eye": {"x": 1.05, "y": 1.25, "z": 0.005}},
                "Mirror": {"eye": {"x": -1.05, "y": 1.25, "z": 0.005}},
                "Birdseye": {"eye": {"x": 0, "y": 0, "z": 1.8}},
                "North View": {"eye": {"x": 0, "y": -2, "z": 0.8}},
                "South View": {"eye": {"x": 0, "y": 2, "z": 0.8}}
            }
            
            # Center the buttons horizontally and match dropdown width
            for preset_name, preset_data in camera_presets.items():
                col1, col2, col3 = st.sidebar.columns([0.1, 0.8, 0.1])
                with col2:
                    if st.button(preset_name, key=f"sidebar_camera_{preset_name}", use_container_width=True):
                        # Add delay for smoothness
                        time.sleep(0.05)
                        selected_preset = preset_data
        
        # Main content area
        if viz_type == "Summary":
            self.render_executive_dashboard(selected_space)
        elif viz_type == "Data Explorer":
            if COMPONENTS_LOADED:
                render_data_explorer(selected_space)
            else:
                st.error("Data Explorer component not available due to import errors")
        elif viz_type == "3D Room Model":
            self.render_3d_model(selected_space, selected_preset)
        elif viz_type == "Frequency Analysis":
            self.render_frequency_analysis(selected_space)
        elif viz_type == "Treatment Simulator":
            self.render_treatment_simulator(selected_space)
        elif viz_type == "Complete Analysis":
            self.render_complete_analysis(selected_space)
    
    def render_executive_dashboard(self, space):
        """Render executive summary dashboard for stakeholders"""
        
        st.header(f"Summary of testing in {space}")
        
        # Load space-specific data
        evidence_data = self.load_space_data(space, 'evidence_degradation')
        treatment_data = self.load_space_data(space, 'treatment_priority')
        
        if evidence_data is None or treatment_data is None:
            st.error(f"⚠️ Cannot load data for {space}. Please ensure data files are generated.")
            return
        
        # Calculate key metrics from actual data
        total_panels = treatment_data['recommended_panels'].apply(lambda x: int(x.split('-')[1].split()[0])).sum()
        estimated_cost = total_panels * 30  # $30 per panel estimate
        
        # STI data handling - only available for Studio 8
        if space == "Studio 8":
            avg_sti_degradation = evidence_data['sti_degradation_percent'].mean()
            worst_position = evidence_data.loc[evidence_data['sti_degradation_percent'].idxmax()]
        else:
            # The Hub - no STI data was recorded
            avg_sti_degradation = None
            worst_position = None
        
        # Critical metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        # Dynamic metrics based on actual data
        with col1:
            if space == "Studio 8" and avg_sti_degradation is not None:
                sti_status = "critical-metric" if avg_sti_degradation > 20 else "warning-metric" if avg_sti_degradation > 10 else "good-metric"
                sti_icon = "🔴" if avg_sti_degradation > 20 else "⚠️" if avg_sti_degradation > 10 else "✅"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{sti_icon} STI DEGRADATION</div>
                    <div class="metric-value {sti_status}">{avg_sti_degradation:.1f}%</div>
                    <p>Average across positions</p>
                    <div class="metric-subtitle">Target: &lt;15%</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # The Hub - no STI data
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">📊 STI DATA</div>
                    <div class="metric-value warning-metric">No Data</div>
                    <p>STI not recorded for The Hub</p>
                    <div class="metric-subtitle">RT60 analysis available</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            if space == "Studio 8" and worst_position is not None:
                worst_pos_name = worst_position['position']
                worst_degradation = worst_position['sti_degradation_percent']
                worst_status = "critical-metric" if worst_degradation > 25 else "warning-metric"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">📍 WORST POSITION</div>
                    <div class="metric-value {worst_status}">{worst_pos_name}</div>
                    <p>{worst_degradation:.1f}% STI degradation</p>
                    <div class="metric-subtitle">Needs priority treatment</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # The Hub - show RT60 based worst position instead
                worst_rt60_pos = evidence_data.loc[evidence_data['RT60_500Hz_increase_percent'].idxmax()]
                worst_rt60_name = worst_rt60_pos['position']
                worst_rt60_increase = worst_rt60_pos['RT60_500Hz_increase_percent']
                rt60_status = "critical-metric" if worst_rt60_increase > 50 else "warning-metric"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">📍 WORST POSITION</div>
                    <div class="metric-value {rt60_status}">{worst_rt60_name}</div>
                    <p>{worst_rt60_increase:.1f}% RT60 increase</p>
                    <div class="metric-subtitle">Needs priority treatment</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            cost_status = "good-metric" if estimated_cost <= 1200 else "warning-metric"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">💰 SOLUTION COST</div>
                <div class="metric-value {cost_status}">${estimated_cost}</div>
                <p>{total_panels} panels recommended</p>
                <div class="metric-subtitle">Budget: $1,200</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Count positions needing urgent treatment
            urgent_positions = len(treatment_data[treatment_data['treatment_urgency'] == 'critical'])
            urgent_status = "critical-metric" if urgent_positions > 2 else "warning-metric" if urgent_positions > 0 else "good-metric"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">🚨 URGENT TREATMENT</div>
                <div class="metric-value {urgent_status}">{urgent_positions}</div>
                <p>Positions need immediate work</p>
                <div class="metric-subtitle">Critical priority</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Hide STI chart for both spaces (STI data quality issues)
        # Position comparison chart
        # st.subheader("STI Degradation by Position")
        # 
        # # Create position comparison chart
        # fig = px.bar(
        #     evidence_data, 
        #     x='position', 
        #     y='sti_degradation_percent',
        #     color='treatment_urgency',
        #     color_discrete_map={'critical': '#e74c3c', 'high': '#f39c12', 'medium': '#27ae60'},
        #     title=f"Speech Transmission Index Degradation - {space}",
        #     labels={'sti_degradation_percent': 'STI Degradation (%)', 'position': 'Measurement Position'}
        # )
        # fig.add_hline(y=15, line_dash="dash", line_color="red", 
        #              annotation_text="Target Threshold (15%)", annotation_position="right")
        # fig.update_layout(height=400, showlegend=True)
        # st.plotly_chart(fig, use_container_width=True)
        
        # Executive summary sections
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            production_impact_content = self.get_production_impact_content(space)
            st.markdown(production_impact_content, unsafe_allow_html=True)
        
        with col_right:
            solution_content = self.get_recommended_solution_content(space)
            st.markdown(solution_content, unsafe_allow_html=True)
    
    def render_3d_model(self, space, selected_preset=None):
        """Render 3D room model with RT60 heatmap"""
        
        # Initialize session state for camera view persistence and 3D model caching
        if "camera_view" not in st.session_state:
            st.session_state.camera_view = None
        if "last_panel_count_3d" not in st.session_state:
            st.session_state.last_panel_count_3d = 25
        if "cached_3d_fig" not in st.session_state:
            st.session_state.cached_3d_fig = None
        if "model_revision_id" not in st.session_state:
            st.session_state.model_revision_id = "model_v1"
        if "last_panel_count" not in st.session_state:
            st.session_state.last_panel_count = 25
        if "cached_rt60_fig" not in st.session_state:
            st.session_state.cached_rt60_fig = None
        if "panel_count" not in st.session_state:
            st.session_state.panel_count = 25
        
        # Two-column header layout matching Frequency Analysis page
        header_col1, header_col2 = st.columns([1, 1])
        
        with header_col1:
            st.info("🎯 **Interactive 3D Model:** Rotate, zoom, and click on measurement positions to explore the acoustic space")
        
        with header_col2:
            # Initialize panel count in session state with space-specific defaults
            if 'panel_count' not in st.session_state:
                default_count = 10 if space == "The Hub" else 25
                st.session_state.panel_count = default_count
            
            # Panel count text input only (matching Frequency Analysis page style)
            current_panel_count = st.number_input(
                label="Panel Count",
                min_value=0,
                max_value=40,
                value=st.session_state.panel_count,
                step=1,
                key="3d_panel_number_input",
                help="Enter panel count directly"
            )
            # Add delay for smoothness
            import time
            time.sleep(0.05)
            # Update session state with typed value
            st.session_state.panel_count = current_panel_count
        
        # Store current panel count for use in visualization
        panel_count = st.session_state.panel_count
        
        # Main visualization area - 3D model and RT60 heatmap side by side
        viz_col1, viz_col2 = st.columns([3, 2])
        
        with viz_col1:
            st.subheader("3D Room Model")
            
            if self.visualizer_3d:
                # Only regenerate 3D model if panel count changed or no cached version exists
                if (st.session_state.cached_3d_fig is None or 
                    st.session_state.last_panel_count_3d != panel_count):
                    
                    if space == "Studio 8":
                        fig = self.visualizer_3d.create_studio8_detailed_model(show_panels=True, panel_count=panel_count)
                    elif space == "The Hub":
                        fig = self.visualizer_3d.create_hub_detailed_model(show_panels=True, panel_count=panel_count)
                    else:
                        st.write(f"3D model not available for {space}")
                        return
                        
                    st.session_state.cached_3d_fig = fig
                    st.session_state.last_panel_count_3d = panel_count
                    # Update revision ID when model actually changes
                    st.session_state.model_revision_id = f"model_v{panel_count}_{hash(str(panel_count))}"
                else:
                    fig = st.session_state.cached_3d_fig
                
                # Preserve camera view from previous interaction or apply preset
                if selected_preset:
                    # Sidebar preset takes priority - update both figure and session state
                    camera_settings = dict(eye=selected_preset["eye"])
                    st.session_state.camera_view = camera_settings
                elif st.session_state.camera_view:
                    # Use preserved camera view
                    camera_settings = st.session_state.camera_view
                else:
                    # Use default camera settings and save them
                    camera_settings = dict(eye=dict(x=1.05, y=1.25, z=0.005))
                    st.session_state.camera_view = camera_settings
                
                # Always apply the camera settings to the figure
                fig.update_layout(
                    scene=dict(
                        camera=camera_settings,
                        aspectmode='data'
                    ),
                    uirevision=st.session_state.model_revision_id  # Preserve UI state with consistent revision ID
                )
                
                # Use a stable key that doesn't change with panel count to preserve interactions
                chart_key = f"3d_model_{space.replace(' ', '_').lower()}_stable"
                st.plotly_chart(fig, use_container_width=True, key=chart_key)
            else:
                st.write("3D visualization not available")
        
        with viz_col2:
            st.subheader("RT60 Heatmap")
            
            if space == "Studio 8" and self.rt60_analyzer:
                # Only regenerate RT60 heatmap if panel count changed
                if (st.session_state.cached_rt60_fig is None or 
                    st.session_state.last_panel_count != panel_count):
                    
                    rt60_fig = self.rt60_analyzer.create_rt60_heatmap(panel_count)
                    st.session_state.cached_rt60_fig = rt60_fig
                    st.session_state.last_panel_count = panel_count
                else:
                    rt60_fig = st.session_state.cached_rt60_fig
                
                # Use a unique key for RT60 chart to maintain its state
                heatmap_key = f"rt60_heatmap_{space.replace(' ', '_').lower()}_{panel_count}"
                st.plotly_chart(rt60_fig, use_container_width=True, key=heatmap_key)
                
                # RT60 analysis summary
                self.render_rt60_summary(panel_count)
            elif space == "The Hub":
                st.info("📊 **RT60 Heatmap for The Hub**")
                st.markdown("""
                **RT60 Analysis Coming Soon**
                
                The Hub's hexagonal geometry with irregular angles (88° and 38°) creates unique acoustic challenges:
                
                - Complex reflection patterns from non-parallel surfaces
                - Modal frequencies influenced by hexagonal dimensions  
                - Treatment optimization requires specialized analysis
                
                **Current Status**: 3D model available, RT60 heatmap analysis in development
                """)
            else:
                st.write("RT60 analysis not available")
    
    def render_rt60_summary(self, panel_count):
        """Render condensed RT60 analysis summary for 3D model page"""
        if not self.rt60_analyzer:
            return
            
        rt60_data = self.rt60_analyzer.calculate_rt60_with_panels(panel_count)
        
        # Calculate key statistics
        all_values = []
        for pos_data in rt60_data.values():
            all_values.extend(pos_data.values())
        
        avg_rt60 = np.mean(all_values)
        min_rt60 = np.min(all_values)
        max_rt60 = np.max(all_values)
        
        # Broadcast standard targets for Studio 8
        target_min, target_max = 0.3, 0.5
        in_target = sum(1 for val in all_values if target_min <= val <= target_max)
        target_percentage = (in_target / len(all_values)) * 100
        
        # Determine status and colors
        if avg_rt60 > 0.65:
            status = "🔴 Needs Treatment"
            status_color = "#e74c3c"
            recommendation = "Target green/blue zones on heatmap"
        elif avg_rt60 < 0.35:
            status = "🔵 Excellent Control"
            status_color = "#3498db"
            recommendation = "Blue zone achieved - professional quality"
        elif avg_rt60 < 0.5:
            status = "🟢 Professional Quality"
            status_color = "#27ae60"
            recommendation = "Green zone - broadcast ready"
        else:
            status = "🟡 Good Progress"
            status_color = "#f39c12"
            recommendation = "Approaching green zones"
        
        # Use Streamlit native components instead of complex HTML
        # Status header
        st.markdown(f"""<div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 249, 250, 0.95)); border: 2px solid {status_color}; border-radius: 12px; margin: 1rem 0;">
        <h4 style="color: {status_color}; margin: 0;">{status}</h4>
        <p style="margin: 0.25rem 0 0 0; color: #666;">{recommendation}</p>
        </div>""", unsafe_allow_html=True)
        
        # Create metrics using columns for better compatibility
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Average RT60",
                value=f"{avg_rt60:.2f}s",
                help="Target: 0.3-0.5s for broadcast quality"
            )
            status_emoji = "✅" if target_min <= avg_rt60 <= target_max else "⚠️" if avg_rt60 > target_max else "🔍"
            st.write(f"{status_emoji} {'Good' if target_min <= avg_rt60 <= target_max else 'Adjust' if avg_rt60 > target_max else 'Monitor'}")
        
        with col2:
            st.metric(
                label="Range",
                value=f"{min_rt60:.2f}s - {max_rt60:.2f}s",
                help="Variation across measurement positions"
            )
            range_emoji = "✅" if (max_rt60 - min_rt60) < 0.2 else "⚠️"
            st.write(f"{range_emoji} {'Tight' if (max_rt60 - min_rt60) < 0.2 else 'Variable'}")
        
        with col3:
            st.metric(
                label="In Target Range",
                value=f"{target_percentage:.0f}%",
                help="Percentage of measurements within 0.3-0.5s target"
            )
            target_emoji = "🎯" if target_percentage >= 80 else "📈" if target_percentage >= 60 else "🔧"
            st.write(f"{target_emoji} {'Excellent' if target_percentage >= 80 else 'Improving' if target_percentage >= 60 else 'Work Needed'}")
        
        # Footer info
        st.info(f"**Target:** 0.3-0.5s for broadcast quality | **Panel Count:** {panel_count} panels")
    
    def render_frequency_analysis(self, space):
        """Render frequency analysis dashboard using specialized explorer"""
        
        # Use the specialized frequency response explorer
        if self.freq_explorer:
            # Check if the method accepts space parameter
            try:
                import inspect
                sig = inspect.signature(self.freq_explorer.render_frequency_explorer)
                if 'space' in sig.parameters:
                    self.freq_explorer.render_frequency_explorer(space)
                else:
                    # Component doesn't support space parameter yet, render without note
                    self.freq_explorer.render_frequency_explorer()
            except Exception as e:
                self.freq_explorer.render_frequency_explorer()
        else:
            st.error("Frequency explorer not available")
    
    def render_treatment_simulator(self, space):
        """Render treatment impact simulator using specialized component"""
        
        # Use the specialized treatment simulator
        if self.treatment_sim:
            # Check if the method accepts space parameter
            try:
                import inspect
                sig = inspect.signature(self.treatment_sim.render_treatment_simulator)
                if 'space' in sig.parameters:
                    self.treatment_sim.render_treatment_simulator(space)
                else:
                    # Component doesn't support space parameter yet, render without note
                    self.treatment_sim.render_treatment_simulator()
            except Exception as e:
                self.treatment_sim.render_treatment_simulator()
        else:
            st.error("Treatment simulator not available")
    
    def render_complete_analysis(self, space):
        """Render complete analysis with all components"""
        
        st.header(f"{space} Complete Acoustic Analysis")
        
        st.info("📊 **Comprehensive Analysis:** All visualization tools and analysis components in one view")
        
        # Render each section
        st.subheader("Executive Dashboard")
        self.render_executive_dashboard(space)
        
        st.markdown("---")
        
        st.subheader("3D Room Model")
        self.render_3d_model(space)
        
        st.markdown("---")
        
        st.subheader("Frequency Analysis")
        self.render_frequency_analysis(space)
        
        st.markdown("---")
        
        st.subheader("Treatment Simulator")
        self.render_treatment_simulator(space)
        
    def get_production_impact_content(self, space):
        """Generate space-specific production impact content with enhanced detail"""
        # Load actual data for this space
        evidence_data = self.load_space_data(space, 'evidence_degradation')
        
        if evidence_data is None:
            return f"<p>⚠️ Data not available for {space}</p>"
        
        # Calculate actual metrics
        critical_positions = len(evidence_data[evidence_data['treatment_urgency'] == 'critical'])
        
        if space == "Studio 8":
            # Studio 8 has STI data
            avg_sti_degradation = evidence_data['sti_degradation_percent'].mean()
            worst_position = evidence_data.loc[evidence_data['sti_degradation_percent'].idxmax()]
            geometry_info = "The dual-zone geometry (Zone A: set volume, Zone B: ceiling cavity) creates modal congestion"
            
            return f"""
            <div class="problem-highlight">
                <h3>PRODUCTION IMPACT - {space}</h3>
                <ul>
                    <li><strong>Speech Intelligibility Crisis:</strong> {avg_sti_degradation:.1f}% average STI degradation from reference standard</li>
                    <li><strong>Worst Performance Area:</strong> {worst_position['position']} position with {worst_position['sti_degradation_percent']:.1f}% degradation</li>
                    <li><strong>Critical Treatment Needed:</strong> {critical_positions} positions require immediate intervention</li>
                    <li><strong>Broadcast Standards Risk:</strong> Performance below EBU R128 and ATSC A/85 quality requirements</li>
                    <li><strong>Professional Impact:</strong> {geometry_info} that degrades speech clarity</li>
                    <li><strong>Viewer Experience Impact:</strong> Poor audio clarity directly affects audience engagement and retention</li>
                    <li><strong>Regulatory Compliance:</strong> Current performance compromises broadcast quality standards</li>
                </ul>
                <p><strong>Critical Risk Assessment:</strong> Professional credibility, audience retention, and regulatory compliance at risk. Immediate acoustic treatment required to achieve broadcast-quality speech intelligibility for sports and magazine-style programming.</p>
            </div>
            """
        else:
            # The Hub - no STI data, focus on RT60 issues
            worst_rt60_pos = evidence_data.loc[evidence_data['RT60_500Hz_increase_percent'].idxmax()]
            avg_rt60_increase = evidence_data['RT60_500Hz_increase_percent'].mean()
            geometry_info = "The hexagonal geometry with irregular angles (88° and 38°) creates complex reflection patterns"
            
            return f"""
            <div class="problem-highlight">
                <h3>PRODUCTION IMPACT - {space}</h3>
                <ul>
                    <li><strong>Reverberation Issues:</strong> {avg_rt60_increase:.1f}% average RT60 increase from ideal broadcast standards</li>
                    <li><strong>Worst Performance Area:</strong> {worst_rt60_pos['position']} position with {worst_rt60_pos['RT60_500Hz_increase_percent']:.1f}% RT60 increase</li>
                    <li><strong>Critical Treatment Needed:</strong> {critical_positions} positions require immediate intervention</li>
                    <li><strong>Speech Clarity Risk:</strong> Excessive reverberation affects broadcast quality (STI data not recorded)</li>
                    <li><strong>Professional Impact:</strong> {geometry_info} that degrades speech clarity</li>
                    <li><strong>Viewer Experience Impact:</strong> Poor acoustic environment affects audience engagement</li>
                    <li><strong>Regulatory Compliance:</strong> RT60 performance may compromise broadcast quality standards</li>
                </ul>
                <p><strong>Critical Risk Assessment:</strong> While STI data wasn't recorded for The Hub, RT60 analysis indicates acoustic treatment needed to achieve broadcast-quality reverberation control for professional programming.</p>
            </div>
            """
            
    def get_recommended_solution_content(self, space):
        """Generate space-specific recommended solution content with enhanced detail"""
        # Load actual data for this space
        treatment_data = self.load_space_data(space, 'treatment_priority')
        
        if treatment_data is None:
            return f"<p>⚠️ Treatment data not available for {space}</p>"
        
        # Calculate actual metrics
        total_panels = treatment_data['recommended_panels'].apply(lambda x: int(x.split('-')[1].split()[0])).sum()
        estimated_cost = total_panels * 30
        critical_positions = len(treatment_data[treatment_data['treatment_urgency'] == 'critical'])
        high_priority = len(treatment_data[treatment_data['treatment_urgency'] == 'high'])
        
        # Get treatment types breakdown
        treatment_types = treatment_data['treatment_type'].value_counts()
        
        geometry_context = "dual-zone (Zone A: set volume, Zone B: ceiling cavity)" if space == "Studio 8" else "hexagonal with irregular angles (88° and 38°)"
        
        return f"""
        <div class="solution-highlight">
            <h3>RECOMMENDED SOLUTIONS - {space}</h3>
            <ul>
                <li><strong>Strategic Panel Placement ({total_panels} Total Panels):</strong>
                    <ul>
                        {''.join([f"<li>{count} positions require {treatment_type}</li>" for treatment_type, count in treatment_types.items()])}
                        <li>Priority focus: {critical_positions} critical positions requiring immediate treatment</li>
                        <li>Secondary treatment: {high_priority} high-priority positions</li>
                    </ul>
                </li>
                <li><strong>Treatment Priority Sequence:</strong>
                    <ul>
                        <li>Phase 1: {critical_positions} critical positions (immediate intervention)</li>
                        <li>Phase 2: {high_priority} high-priority positions (secondary wave)</li>
                        <li>Phase 3: Remaining positions for optimal performance</li>
                    </ul>
                </li>
                <li><strong>Technical Implementation:</strong>
                    <ul>
                        <li>Roxul panels (60kg/m³ density) for broadband absorption</li>
                        <li>NRC ratings: 1.10-1.20 for maximum effectiveness</li>
                        <li>Optimized for {geometry_context} geometry</li>
                        <li>Coverage: 30-40% surface area for optimal balance</li>
                    </ul>
                </li>
                <li><strong>Budget Analysis:</strong> ${estimated_cost} CAD ({total_panels} panels @ $30 each) - {'✅ Within' if estimated_cost <= 1200 else '⚠️ Over'} $1,200 budget</li>
                <li><strong>Expected Performance:</strong> Professional broadcast standards, EBU R128 compliance, optimized speech intelligibility</li>
            </ul>
        </div>
        """

# Main application
def main():
    # Set page config for wide layout
    st.set_page_config(
        page_title="CBC Acoustic Analysis Dashboard",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply simplified CSS styling
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
    
    # Show component error if any
    if COMPONENT_ERROR:
        st.error(COMPONENT_ERROR)
    
    # Initialize and render dashboard
    dashboard = AcousticDashboard()
    dashboard.render_dashboard()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import streamlit as st
        st.error("Dashboard failed to load.")
        st.text(str(e))
        import traceback
        st.code(traceback.format_exc())
        raise