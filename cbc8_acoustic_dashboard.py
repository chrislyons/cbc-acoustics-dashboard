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
        /* background: linear-gradient(90deg, #e74c3c, #ffffff, #e74c3c); */
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: var(--text-primary);
        /* box-shadow: 0 4px 15px rgba(0,0,0,0.1); */
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
    
    /* Hide sidebar collapse button - keep sidebar always visible */
    [data-testid="collapsedControl"] {
        display: none !important;
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
        
        # Header with CBC logo - aligned layout
        col1, col2 = st.columns([0.75, 5.25])
        
        with col1:
            # CBC Logo - larger and with top margin for vertical alignment
            st.markdown('<div style="margin-top: 20px;" "margin-left: 20px"></div>', unsafe_allow_html=True)
            st.image('assets/cbc_gem_logo.png', width=240)
        
        with col2:
            # Main header with reduced left padding for closer alignment
            st.markdown("""
            <div class="main-header" style="padding-left: 15px; margin-top: 0;">
                <h1 style="margin-bottom: 5px;">CBC Sports 8th Floor Acoustics Dashboard</h1>
                <p style="margin-top: 0;">Interactive visualizations of Studio 8 &amp; The Hub acoustic analysis</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Sidebar controls
        st.sidebar.header("Dashboard Controls")
        
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
            default_count = 8 if selected_space == "The Hub" else 25
            st.session_state.panel_count = default_count
            # Force rerun to refresh all components
            st.rerun()
        
        # Visualization type with persistence
        page_options = ["Summary", "Data Explorer", "3D Room Model", "Frequency Response", "Treatment Simulator", "Complete Analysis"]
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
        elif viz_type == "Frequency Response":
            self.render_frequency_analysis(selected_space)
        elif viz_type == "Treatment Simulator":
            self.render_treatment_simulator(selected_space)
        elif viz_type == "Complete Analysis":
            self.render_complete_analysis(selected_space)
    
    def render_executive_dashboard(self, space):
        """Render executive summary dashboard for stakeholders"""
        
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
        
        # Hidden - Critical metrics row (metric cards hidden per user request)
        # col1, col2, col3, col4 = st.columns(4)
        # 
        # # Dynamic metrics based on actual data
        # with col1:
        #     if space == "Studio 8" and avg_sti_degradation is not None:
        #         sti_status = "critical-metric" if avg_sti_degradation > 20 else "warning-metric" if avg_sti_degradation > 10 else "good-metric"
        #         sti_icon = "🔴" if avg_sti_degradation > 20 else "⚠️" if avg_sti_degradation > 10 else "✅"
        #         st.markdown(f"""
        #         <div class="metric-card">
        #             <div class="metric-label">{sti_icon} STI DEGRADATION</div>
        #             <div class="metric-value {sti_status}">{avg_sti_degradation:.1f}%</div>
        #             <p>Average across positions</p>
        #             <div class="metric-subtitle">Target: &lt;15%</div>
        #         </div>
        #         """, unsafe_allow_html=True)
        #     else:
        #         # The Hub - no STI data
        #         st.markdown(f"""
        #         <div class="metric-card">
        #             <div class="metric-label">📊 STI DATA</div>
        #             <div class="metric-value warning-metric">No Data</div>
        #             <p>STI not recorded for The Hub</p>
        #             <div class="metric-subtitle">RT60 analysis available</div>
        #         </div>
        #         """, unsafe_allow_html=True)
        # 
        # with col2:
        #     if space == "Studio 8" and worst_position is not None:
        #         worst_pos_name = worst_position['position']
        #         worst_degradation = worst_position['sti_degradation_percent']
        #         worst_status = "critical-metric" if worst_degradation > 25 else "warning-metric"
        #         st.markdown(f"""
        #         <div class="metric-card">
        #             <div class="metric-label">📍 WORST POSITION</div>
        #             <div class="metric-value {worst_status}">{worst_pos_name}</div>
        #             <p>{worst_degradation:.1f}% STI degradation</p>
        #             <div class="metric-subtitle">Needs priority treatment</div>
        #         </div>
        #         """, unsafe_allow_html=True)
        #     else:
        #         # The Hub - show RT60 based worst position instead
        #         worst_rt60_pos = evidence_data.loc[evidence_data['RT60_500Hz_increase_percent'].idxmax()]
        #         worst_rt60_name = worst_rt60_pos['position']
        #         worst_rt60_increase = worst_rt60_pos['RT60_500Hz_increase_percent']
        #         rt60_status = "critical-metric" if worst_rt60_increase > 50 else "warning-metric"
        #         st.markdown(f"""
        #         <div class="metric-card">
        #             <div class="metric-label">📍 WORST POSITION</div>
        #             <div class="metric-value {rt60_status}">{worst_rt60_name}</div>
        #             <p>{worst_rt60_increase:.1f}% RT60 increase</p>
        #             <div class="metric-subtitle">Needs priority treatment</div>
        #         </div>
        #         """, unsafe_allow_html=True)
        # 
        # with col3:
        #     cost_status = "good-metric" if estimated_cost <= 1200 else "warning-metric"
        #     st.markdown(f"""
        #     <div class="metric-card">
        #         <div class="metric-label">💰 SOLUTION COST</div>
        #         <div class="metric-value {cost_status}">${estimated_cost}</div>
        #         <p>{total_panels} panels recommended</p>
        #         <div class="metric-subtitle">Budget: $1,200</div>
        #     </div>
        #     """, unsafe_allow_html=True)
        # 
        # with col4:
        #     # Count positions needing urgent treatment
        #     urgent_positions = len(treatment_data[treatment_data['treatment_urgency'] == 'critical'])
        #     urgent_status = "critical-metric" if urgent_positions > 2 else "warning-metric" if urgent_positions > 0 else "good-metric"
        #     st.markdown(f"""
        #     <div class="metric-card">
        #         <div class="metric-label">🚨 URGENT TREATMENT</div>
        #         <div class="metric-value {urgent_status}">{urgent_positions}</div>
        #         <p>Positions need immediate work</p>
        #         <div class="metric-subtitle">Critical priority</div>
        #     </div>
        #     """, unsafe_allow_html=True)
        
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
        
        # Executive summary section using native Streamlit components
        self.render_summary_content(space)
    
    def render_summary_content(self, space):
        """Render comprehensive acoustic treatment summary using native Streamlit components"""
        
        st.markdown("""
        <div class="solution-highlight">
        <h3>Summary of Acoustic Treatment Recommendations – Studio 8 & The Hub</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**Version:** 1.01  \n**Prepared:** July 31, 2025  \n**Data Basis:** July 15 test data @ 85dB SPL (pink noise) + 100dB SPL (sine sweep)")
        
        st.subheader("Summary")
        st.write("Presenting acoustic analysis and treatment priorities for **CBC Studio 8** and **The Hub**, based on calibrated Smaart test data, modal analysis, and STI degradation modelling. Both spaces exhibit unique challenges in speech clarity, with tailored treatment plans required to meet broadcast standards.")
        
        st.subheader("Interactive Dashboard")
        #st.write("This dashboard supports decision-making by visualizing treatment impacts: ")
        st.write("This comprehensive interactive dashboard integrates multiple analysis tools to support acoustic treatment decision-making. Built on empirical measurement data from both spaces, the dashboard provides real-time visualization of treatment impacts, cost modeling, and performance optimization. Stakeholders can explore acoustic characteristics, simulate various treatment scenarios, and validate investment decisions through quantitative analysis of frequency response, reverberation control, and speech intelligibility metrics.")
        st.write("- **3D Room Models** with clickable measurement positions and real-time panel placement visualization")
        st.write("- **Frequency Response Explorer** with magnitude, phase, and modal stack analysis")
        st.write("- **Treatment Simulator** with cost calculator and panel effectiveness modeling")
        st.write("- **RT60 Heatmap Analyzer** showing before/after acoustic performance")
        st.write("- **STI Degradation Analysis** with treatment priority recommendations.") 
        st.write("The dashboard processes actual Smaart measurement data from both spaces, enabling stakeholders to explore acoustic characteristics, simulate treatment scenarios, and validate investment decisions through data-driven insights.")
        st.write("**TRY:** Adding/Removing panels in the **3D Room Modeller** to view placement prioritization, Filtering by specific measurement positions in the **Data Explorer**, adjusting Panel Count in the **Treatment Simulator** to see effect on RT60 values.")

        st.subheader("Proposed Panel Construction")
        st.write("- Roxul SAFE'N'SOUND® (etc.) fire-safe and non-toxic mineral wool batts (60kg/m³ density, NRC ratings: 1.10-1.20) for broadband acoustic absorption; various thicknesses (2\", 3\", 5.5\")")
        st.write("- Pine strapping to build boxes around the mineral wool batts, matching width to thickness of batts")
        st.write("- Landscaping fabric to wrap batts and pine frames, stapled taut to offer both rigidity and acoustic transparency")
        st.write("- (optional) Black poly-cotton fabric to wrap panels for camera considerations")
        
        st.subheader("Materials Budget (shared June 20, 2025)")
        
        # Materials budget table using pandas
        import pandas as pd
        budget_data = {
            'Item': ['Roxul Mineral Wool', 'Wood and Mounting Hardware', 'Landscaping Fabric, Black Fabric', '**Total Estimated Cost before HST**'],
            'Description & Quantity': [
                '4 packs of 2"/3"/5.5" x 2\' x 4\' panels (48 batts @ $12.50 each)',
                'Furring strips, Z-clips, screws, etc.',
                '100 feet x 60" wide (~$3 per foot)',
                ''
            ],
            'Unit Cost (CAD)': ['~$600', '~$300', '~$300', ''],
            'Total (CAD)': ['$600', '$300', '$300', '**$1,200**']
        }
        budget_df = pd.DataFrame(budget_data)
        st.table(budget_df.style.hide(axis='index'))
        
        st.subheader("Studio 8 (Television Studio)")
        
        st.write("**Diagnostics**")
        st.write("- Current acoustic environment produces **extremely poor speech intelligibility in broadcast-critical areas** which we can treat by absorbing reflections")
        st.write("- **Studio 8 contains a symmetrical 24' x 24' volume** at the intersection of **reflective set area (Zone A)** with bright early reflections, **reverberant ceiling cavity (Zone B)** with long decay tails")
        st.write("- **Severe STI degradation** at corners (25–34%), a primary obstacle presented by **Modal clusters** between 20–250 Hz due to stacked height modes interacting above and below the grid")
        st.write("- **Ambient HVAC noise** ongoing in surrounding office area, could be dampened slightly by panel treatment (secondary objective)")
        
        st.write("**Treatment Plan – Studio 8**")
        
        # Studio 8 treatment table
        studio8_data = {
            'Location': ['Ceiling Corner Bass Traps', 'Ceiling Clouds', 'Desk Clouds', 'North Wall / NE Corner'],
            'Panels': ['4 panels, double-batted', '12–14 panels', '3 panels', '5 panels'],
            'Type': ['Bass traps (11" thickness)', 'Broadband absorbers (5.5" thickness)', 'Clouds (2" thickness)', 'Broadband/mid absorbers (3")'],
            'Priority': ['1', '2', '3', '4']
        }
        studio8_df = pd.DataFrame(studio8_data)
        st.table(studio8_df.style.hide(axis='index'))
        
        st.write("**Studio 8 Total Estimate**")
        st.write("- **24–30 batts** required = ~ $750 in materials")
        st.write("- **Focus:** treating low and mid energy buildup in the ceiling area and corners of the studio to address modal buildup throughout the spectrum")
        st.write("- **Effectiveness:** Up to **18dB reduction** in modal hot zones")
        
        st.subheader("The Hub (Digital Studio)")
        
        st.write("**Diagnostics**")
        st.write("- **Localized clarity issues** caused by glass surfaces enclosing a small space at odd angles")
        st.write("- **Modal issues manageable** with strategic softening in off-camera areas")
        
        st.write("**Treatment Plan – The Hub**")
        
        # The Hub treatment table
        hub_data = {
            'Position': ['Ceiling Clouds', 'East Wall', 'NE Wall', 'NW Wall', 'LED Panels?', 'North Wall'],
            'Panels': ['2 panels', '2 panels', '2 panels', '2 panels', '4 panels', '2 panels'],
            'Purpose': ['Midrange absorbers (3" thick)', 'Broadband absorbers (5.5" thick)', 'Ceiling clouds (3" thick)', 'Wall panels (3" thick)', 'Behind LED Fixtures? (2" thick)', 'Broadband absorbers (5.5" thick)'],
            'Priority': ['1', '2', '3', '4', '5', '6']
        }
        hub_df = pd.DataFrame(hub_data)
        st.table(hub_df.style.hide(axis='index'))
        
        st.write("**The Hub Total Estimate**")
        st.write("- **10–14 batts** required = ~ $350 in materials")
        st.write("- **Focus:** maximizing absorptive surface area coverage in off-camera areas to manage modal stacks in odd acoustic space")
        st.write("- **Effectiveness:** ~8–12dB smoothing in problem regions")
        
        st.subheader("Cross-Space Notes")
        st.write("- STI degradation values for Studio 8 are simulated based on RT60, EDT, D/R, C10, C35, C50, C80 values recorded in Smaart")
        st.write("- Treatment plans reflect both **magnitude-based frequency response** and **speech intelligibility deterioration**")
        st.write("- **No over-treatment** recommended: high-band brightness preserved, low- and mid-band modal stacks attenuated")
        st.write("- Panels should be strategically placed, not symmetrical, to break up modal symmetry and avoid flutter echoes")
        
        st.subheader("Glossary of Terms")
        
        st.write("**RT60 (Reverberation Time)**")
        st.write("Time (seconds) it takes for sound energy in a room to decrease by 60 dB after sound stops; measures reverberation.")
        
        st.write("**STI (Speech Transmission Index)**")
        st.write("Numerical metric (0–1) assessing speech intelligibility based on signal modulation integrity; higher STI indicates clearer speech.")
        
        st.write("**IR (Impulse Response)**")
        st.write("Time-domain response capturing how an acoustic environment reacts to an impulse; basis for analyzing reflections and reverberation.")
        
        st.write("**ETC (Energy-Time Curve)**")
        st.write("Graph showing sound energy arrival over time, derived from impulse response; used to identify direct sound, reflections, and acoustic anomalies.")
        
        st.write("**C10 (Clarity Index, 10 ms)**")
        st.write("Ratio (dB) of early sound energy (within 10 ms) to late energy, measuring musical clarity; higher values indicate clearer musical articulation.")
        
        st.write("**C35 (Clarity Index, 35 ms)**")
        st.write("Similar to C30 but using 35 ms threshold; less common intermediate clarity metric.")
        
        st.write("**C50 (Clarity Index, 50 ms)**")
        st.write("Ratio (dB) of early sound energy (within 50 ms) to late energy, quantifying speech clarity; higher values correlate with clearer speech intelligibility.")
        
        st.write("**C80 (Clarity Index, 80 ms)**")
        st.write("Ratio (dB) of early sound energy (within 80 ms) to late energy, used to assess musical clarity and definition.")
        
        st.write("**EDT (Early Decay Time)**")
        st.write("Time (seconds) for initial 10 dB sound decay extrapolated to 60 dB; correlates strongly with perceived reverberation.")
    
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
            if space == "The Hub":
                st.info("🎯 **Interactive 3D Model:** Explore The Hub's hexagonal geometry and panel placement optimization")
            else:
                st.info("🎯 **Interactive 3D Model:** Rotate, zoom, and click on measurement positions to explore the acoustic space")
        
        with header_col2:
            # Initialize panel count in session state with space-specific defaults
            if 'panel_count' not in st.session_state:
                default_count = 8 if space == "The Hub" else 25
                st.session_state.panel_count = default_count
            
            # Panel count text input with space-specific max values
            max_panels = 16 if space == "The Hub" else 32
            current_panel_count = st.number_input(
                label="Panel Count",
                min_value=0,
                max_value=max_panels,
                value=st.session_state.panel_count,
                step=1,
                key="3d_panel_number_input",
                help=f"Enter panel count directly (max {max_panels} for {space})"
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
                
                # Create theoretical Hub RT60 heatmap based on panel count
                hub_rt60_fig = self.create_hub_theoretical_heatmap(panel_count)
                if hub_rt60_fig:
                    heatmap_key = f"rt60_heatmap_hub_{panel_count}"
                    st.plotly_chart(hub_rt60_fig, use_container_width=True, key=heatmap_key)
                    
                    # Hub-specific RT60 analysis summary
                    self.render_hub_rt60_summary(panel_count)
                else:
                    st.warning("Unable to generate RT60 heatmap for The Hub")
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
        target_min, target_max = 0.3, 0.4
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
                help="Target: 0.3-0.4s for broadcast quality"
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
                help="Percentage of measurements within 0.3-0.4s target"
            )
            target_emoji = "🎯" if target_percentage >= 80 else "📈" if target_percentage >= 60 else "🔧"
            st.write(f"{target_emoji} {'Excellent' if target_percentage >= 80 else 'Improving' if target_percentage >= 60 else 'Work Needed'}")
        
        # Footer info
        st.info(f"**Target:** 0.3-0.4s for broadcast quality | **Panel Count:** {panel_count} panels")
    
    def create_hub_theoretical_heatmap(self, panel_count=0):
        """Create RT60 heatmap for The Hub using real measurement data"""
        import plotly.graph_objects as go
        import numpy as np
        from pathlib import Path
        
        # Real Hub measurement data from Smaart logs
        hub_rt60_data = self.load_hub_rt60_data()
        
        if not hub_rt60_data:
            st.error("Unable to load Hub RT60 measurement data")
            return None
        
        # Apply panel effect to real measurements
        panel_reduction_factor = min(0.6, panel_count * 0.04)  # 4% per panel, max 60%
        
        # Frequency bands (matching Studio 8)
        frequencies = ['125Hz', '250Hz', '500Hz', '1kHz', '2kHz', '4kHz', '8kHz']
        positions = list(hub_rt60_data.keys())
        
        # Create heatmap data with panel adjustments
        z_values = []
        hover_text = []
        
        for freq in frequencies:
            row_values = []
            hover_row = []
            
            for pos_name in positions:
                if freq in hub_rt60_data[pos_name]:
                    base_rt60 = hub_rt60_data[pos_name][freq]
                    # Apply panel reduction
                    adjusted_rt60 = base_rt60 * (1 - panel_reduction_factor)
                    row_values.append(adjusted_rt60)
                    hover_row.append(f"{pos_name}<br>{freq}: {adjusted_rt60:.2f}s<br>Panels: {panel_count}")
                else:
                    row_values.append(0.4)  # fallback
                    hover_row.append(f"{pos_name}<br>{freq}: No data<br>Panels: {panel_count}")
            
            z_values.append(row_values)
            hover_text.append(hover_row)
        
        # Create heatmap with Studio 8's exact colorscale
        fig = go.Figure(data=go.Heatmap(
            z=z_values,
            x=positions,
            y=frequencies,
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=hover_text,
            showscale=True,
            colorscale=[
                [0.0, '#000080'],    # Dark blue for very low RT60 (0.15s)
                [0.05, '#003399'],   # Deep blue
                [0.08, '#0066CC'],   # Medium blue
                [0.10, '#3399FF'],   # Lighter blue
                [0.12, '#4DA6FF'],   # Blue-green transition
                [0.13, '#40C040'],   # GREEN START - Hub ideal range (0.2s)
                [0.16, '#48C848'],   # Early green
                [0.18, '#50D050'],   # Green progression
                [0.22, '#58D858'],   # Target green center (0.25s)
                [0.27, '#60E060'],   # Center green
                [0.29, '#68E868'],   # Late green
                [0.31, '#70F070'],   # GREEN END - Hub ideal range (0.3s)
                [0.33, '#80FF80'],   # Light green transition
                [0.35, '#90FF90'],   # Lighter green
                [0.37, '#A0FFA0'],   # Green-yellow bridge
                [0.39, '#CCFF88'],    # Yellow-green
                [0.43, '#EEFF77'],   # Soft yellow-green
                [0.46, '#FFFF66'],   # Standard yellow
                [0.50, '#FFEE55'],   # Gentle yellow
                [0.52, '#FFD700'],   # Gold yellow
                [0.55, '#FFCC33'],   # Gold transition
                [0.60, '#FFA500'],   # Orange
                [0.66, '#FF8C00'],   # Dark orange
                [0.72, '#FF6347'],   # Tomato/red-orange
                [0.77, '#FF4500'],    # Red-orange
                [0.83, '#FF3300'],   # Bright red
                [0.88, '#E60000'],    # Deep red
                [1.0, '#CC0000']     # DEEPEST RED at 0.7s
            ],
            zmin=0.15,   # Minimum possible with maximum treatment
            zmax=0.7,    # Maximum expected from measurements
            colorbar=dict(
                title=dict(
                    text="RT60 (seconds)",
                    side="right"
                ),
                tickmode="linear",
                tick0=0.2,
                dtick=0.1
            )
        ))
        
        fig.update_layout(
            title=f"The Hub RT60 Analysis - {panel_count} Panels (Real Data)",
            xaxis_title="Measurement Position",
            yaxis_title="Frequency",
            height=400,
            font=dict(size=12)
        )
        
        return fig
    
    def load_hub_rt60_data(self):
        """Load actual RT60 measurements from Hub Smaart log files"""
        from pathlib import Path
        
        # Path to Hub Smaart logs
        hub_path = Path('data/raw/250715-smaartLogs/TheHub')
        
        # Mapping from file names to position names
        file_to_position = {
            'TheHub-Chair1-64k.txt': 'Chair1',
            'TheHub-Chair2-64k.txt': 'Chair2',
            'TheHub-MidRoom-64k.txt': 'MidRoom',
            'TheHub-BackCorner-64k.txt': 'BackCorner',
            'TheHub-CeilingCorner-64k.txt': 'CeilingCorner'
        }
        
        hub_data = {}
        
        for filename, position in file_to_position.items():
            file_path = hub_path / filename
            if not file_path.exists():
                continue
                
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                # Parse RT60 values (same format as Studio 8)
                position_data = {}
                for line in lines:
                    if line.startswith('Oct\t') and 'Hz' in line:
                        parts = line.strip().split('\t')
                        if len(parts) >= 3:
                            freq_str = parts[1]
                            rt60_str = parts[2]
                            
                            try:
                                rt60_val = float(rt60_str)
                                if rt60_val > 0:  # Valid measurement
                                    # Map frequencies to match our labels
                                    freq_map = {'125Hz': '125Hz', '250Hz': '250Hz', '500Hz': '500Hz', 
                                              '1kHz': '1kHz', '2kHz': '2kHz', '4kHz': '4kHz', '8kHz': '8kHz'}
                                    if freq_str in freq_map:
                                        position_data[freq_map[freq_str]] = rt60_val
                            except ValueError:
                                continue
                
                if position_data:
                    hub_data[position] = position_data
                    
            except Exception as e:
                st.warning(f"Error loading Hub data from {filename}: {e}")
                continue
        
        return hub_data
    
    def render_hub_rt60_summary(self, panel_count):
        """Render RT60 analysis summary specific to The Hub"""
        # Calculate theoretical averages
        base_avg = 0.59  # Hub baseline average
        panel_reduction = min(0.6, panel_count * 0.04)  # 4% per panel
        current_avg = base_avg * (1 - panel_reduction)
        
        # Determine status for Hub (0.2-0.3s target range)
        if current_avg >= 0.44:
            status = "🔴 Needs Treatment"
            status_color = "#e74c3c"
            recommendation = "Add panels to problem areas shown in red"
        elif current_avg < 0.28:
            status = "🔵 Excellent Control"
            status_color = "#3498db"
            recommendation = "Optimal RT60 achieved for compact space"
        elif current_avg <= 0.38:
            status = "🟢 Target Range"
            status_color = "#27ae60"
            recommendation = "Ideal RT60 for compact broadcast space"
        else:
            status = "🟡 Moderate"
            status_color = "#f39c12"
            recommendation = "Additional panels recommended"
        
        # Status display
        st.markdown(f"""<div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 249, 250, 0.95)); border: 2px solid {status_color}; border-radius: 12px; margin: 1rem 0;">
        <h4 style="color: {status_color}; margin: 0;">{status}</h4>
        <p style="margin: 0.25rem 0 0 0; color: #666;">{recommendation}</p>
        </div>""", unsafe_allow_html=True)
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Average RT60",
                value=f"{current_avg:.2f}s",
                delta=f"{-(base_avg - current_avg):.2f}s" if panel_count > 0 else None,
                help="Average reverberation time across all frequencies"
            )
        
        with col2:
            improvement_pct = panel_reduction * 100
            st.metric(
                label="Improvement",
                value=f"{improvement_pct:.0f}%",
                help="RT60 reduction from baseline"
            )
        
        with col3:
            target_range = "0.2-0.3s"
            in_target = "Yes" if 0.2 <= current_avg <= 0.3 else "No"
            st.metric(
                label="Target Range",
                value=in_target,
                help=f"Hub target: {target_range} for compact space"
            )
        
        st.info(f"**Hub Target:** 0.2-0.3s (compact space) | **Panel Count:** {panel_count} panels")
    
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
                st.error(f"Error rendering frequency explorer: {e}")
                # Don't call again - this was causing duplicate key errors
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
        
        # Render each section
        self.render_executive_dashboard(space)
        
        st.markdown("---")
        
        st.subheader("3D Room Model")
        self.render_3d_model(space)
        
        st.markdown("---")
        
        st.subheader("Frequency Response")
        self.render_frequency_analysis(space)
        
        st.markdown("---")
        
        st.subheader("Treatment Simulator")
        self.render_treatment_simulator(space)
        
    def get_summary_content(self, space):
        """Generate comprehensive acoustic treatment summary for both spaces using native Streamlit components"""
        # Instead of returning complex HTML, we'll render the content directly in the calling method
        return None

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