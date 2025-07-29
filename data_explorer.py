#!/usr/bin/env python3
"""
Data Explorer Component for CBC Studio 8 & Hub Acoustic Analysis Dashboard
Provides comprehensive access to all data points from generated CSV files
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

class DataExplorer:
    def __init__(self, data_dir="data/generated"):
        self.data_dir = Path(data_dir)
        self.datasets = {}
        self.dataset_friendly_names = {}  # Maps filename to friendly name
        self.unified_data = None
        
    def load_all_datasets(self):
        """Load all CSV files from the generated data directory"""
        if not self.data_dir.exists():
            st.error(f"Data directory not found: {self.data_dir}")
            return False
            
        csv_files = list(self.data_dir.glob("*.csv"))
        if not csv_files:
            st.warning("No CSV files found in data directory")
            return False
            
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                
                # Clean up column names to be human-friendly
                df = self._clean_column_names(df)
                
                # Add metadata columns
                df['Source File'] = csv_file.name
                df['Dataset Type'] = self._classify_dataset(csv_file.name)
                df['Space'] = self._extract_space(csv_file.name)
                df['Timestamp'] = self._extract_timestamp(csv_file.name)
                
                # Generate friendly name for this dataset
                friendly_name = self._generate_friendly_name(csv_file.name)
                self.dataset_friendly_names[csv_file.name] = friendly_name
                
                self.datasets[csv_file.name] = df
            except Exception as e:
                st.warning(f"Error loading {csv_file.name}: {e}")
                continue
                
        return len(self.datasets) > 0
    
    def _clean_column_names(self, df):
        """Convert technical column names to human-friendly labels"""
        column_mapping = {
            # Frequency response columns
            'frequency_hz': 'Frequency (Hz)',
            'Frequency_Hz': 'Frequency (Hz)',
            'magnitude_db': 'Magnitude (dB)',
            'Magnitude_dB': 'Magnitude (dB)', 
            'phase_deg': 'Phase (°)',
            'Phase_deg': 'Phase (°)',
            'position': 'Measurement Position',
            'Color': 'Plot Color',
            'STI': 'Speech Transmission Index',
            'STI_Degradation_%': 'STI Degradation (%)',
            
            # Modal analysis columns
            'Stack_ID': 'Modal Stack ID',
            'Frequency_Range_Hz': 'Frequency Range (Hz)',
            'Primary_Mode_Hz': 'Primary Mode (Hz)',
            'Mode_Count': 'Mode Count',
            'Mode_Types': 'Mode Types',
            'Zone_A_Impact': 'Zone A Impact',
            'Zone_B_Impact': 'Zone B Impact',
            'Treatment_Priority': 'Treatment Priority',
            
            # Treatment planning columns
            'drape_absorption_coeff': 'Drape Absorption Coefficient',
            'lost_absorption_units': 'Lost Absorption Units',
            'panel_absorption_coeff': 'Panel Absorption Coefficient',
            'equivalent_panels_needed': 'Equivalent Panels Needed',
            'priority': 'Priority',
            
            # Common columns
            'frequency': 'Frequency (Hz)',
        }
        
        # Apply the mapping
        df = df.rename(columns=column_mapping)
        
        # Clean up any remaining underscores and capitalize
        new_columns = {}
        for col in df.columns:
            if col not in column_mapping.values():  # Don't re-process already mapped columns
                # Replace underscores with spaces and title case
                clean_name = col.replace('_', ' ').title()
                new_columns[col] = clean_name
        
        df = df.rename(columns=new_columns)
        return df
    
    def _classify_dataset(self, filename):
        """Classify dataset type based on filename"""
        if "Modal_Stack" in filename:
            return "Modal Analysis"
        elif "Frequency_Response" in filename:
            return "Frequency Response"
        elif "Treatment_Priority" in filename:
            return "Treatment Planning"
        elif "Drape_Compensation" in filename:
            return "Measurement Correction"
        elif "Evidence_Degradation" in filename:
            return "Evidence Analysis"
        else:
            return "Other"
    
    def _extract_space(self, filename):
        """Extract space identifier from filename"""
        if "Studio8" in filename:
            return "Studio 8"
        elif "TheHub" in filename:
            return "The Hub"
        else:
            return "Unknown"
    
    def _extract_timestamp(self, filename):
        """Extract timestamp from filename (YYMMDD format)"""
        import re
        match = re.match(r'(\d{6})', filename)
        if match:
            return match.group(1)
        return "Unknown"
    
    def _generate_friendly_name(self, filename):
        """Generate human-friendly names for dataset files"""
        # Remove file extension
        name = filename.replace('.csv', '')
        
        # Parse the standard format: YYMMDD-SpaceID-Description
        import re
        
        # Extract components
        timestamp_match = re.match(r'(\d{6})', name)
        timestamp = timestamp_match.group(1) if timestamp_match else ""
        
        space = self._extract_space(filename)
        dataset_type = self._classify_dataset(filename)
        
        # Create friendly descriptions based on content
        if "Complete_Frequency_Response" in filename:
            return f"{space} - Complete Frequency Response ({timestamp})"
        elif "Detailed_Frequency_Response" in filename:
            return f"{space} - Detailed Frequency Response ({timestamp})"
        elif "Frequency_Response_Data" in filename:
            return f"{space} - Frequency Response Data ({timestamp})"
        elif "Modal_Stack_Analysis" in filename:
            return f"{space} - Modal Stack Analysis ({timestamp})"
        elif "Treatment_Priority_Matrix" in filename:
            return f"{space} - Treatment Priority Matrix ({timestamp})"
        elif "Drape_Compensation_Evidence" in filename:
            return f"{space} - Drape Compensation Evidence ({timestamp})"
        elif "Evidence_Degradation_Analysis" in filename:
            return f"{space} - Evidence Degradation Analysis ({timestamp})"
        else:
            # Fallback: clean up the description part
            description_part = name.split('-', 3)[-1] if '-' in name else name
            description = description_part.replace('_', ' ').title()
            return f"{space} - {description} ({timestamp})" if timestamp else f"{space} - {description}"
    
    def create_unified_dataset(self):
        """Create a unified dataset from all loaded CSV files"""
        if not self.datasets:
            return None
            
        unified_rows = []
        
        for filename, df in self.datasets.items():
            for _, row in df.iterrows():
                unified_row = {
                    'source_file': filename,
                    'dataset_type': row.get('dataset_type', 'Unknown'),
                    'space': row.get('space', 'Unknown'),
                    'timestamp': row.get('timestamp', 'Unknown'),
                    'row_index': _,
                }
                
                # Add all original columns with prefixes to avoid conflicts
                for col in df.columns:
                    if col not in ['source_file', 'dataset_type', 'space', 'timestamp']:
                        unified_row[col] = row[col]
                
                unified_rows.append(unified_row)
        
        self.unified_data = pd.DataFrame(unified_rows)
        return self.unified_data
    
    def render_summary_stats(self):
        """Render summary statistics section"""
        if not self.datasets:
            st.warning("No data loaded")
            return
            
        col1, col2, col3, col4 = st.columns(4)
        
        total_files = len(self.datasets)
        total_rows = sum(len(df) for df in self.datasets.values())
        dataset_types = set()
        spaces = set()
        
        for df in self.datasets.values():
            if 'dataset_type' in df.columns:
                dataset_types.update(df['dataset_type'].unique())
            if 'space' in df.columns:
                spaces.update(df['space'].unique())
        
        with col1:
            st.metric("Total Files", total_files)
        with col2:
            st.metric("Total Data Points", total_rows)
        with col3:
            st.metric("Dataset Types", len(dataset_types))
        with col4:
            st.metric("Spaces Analyzed", len(spaces))
    
    def render_dataset_overview(self):
        """Render dataset overview table"""
        if not self.datasets:
            return
            
        overview_data = []
        for filename, df in self.datasets.items():
            overview_data.append({
                'File': filename,
                'Rows': len(df),
                'Columns': len(df.columns),
                'Type': df['dataset_type'].iloc[0] if 'dataset_type' in df.columns else 'Unknown',
                'Space': df['space'].iloc[0] if 'space' in df.columns else 'Unknown',
                'Timestamp': df['timestamp'].iloc[0] if 'timestamp' in df.columns else 'Unknown'
            })
        
        overview_df = pd.DataFrame(overview_data)
        st.dataframe(overview_df, use_container_width=True)
    
    def render_data_table(self, selected_space=None):
        """Render the main filterable data table"""
        if not self.datasets:
            st.warning("No data to display")
            return
        
        # Use master space selection or default to Studio 8
        if selected_space is None:
            selected_space = "Studio 8"
        
        # Smart default selection - prioritize Modal Stack for each space
        def get_smart_defaults(selected_space):
            """Get smart default file selection based on selected space"""
            defaults = []
            file_list = list(space_filtered_datasets.keys())
            
            # Priority 1: Modal Stack Analysis for the selected space
            modal_files = [f for f in file_list if "Modal_Stack" in f]
            if modal_files:
                # Get the latest modal stack file for this space
                modal_files.sort(reverse=True)
                defaults.append(modal_files[0])
            
            return defaults
        
        # Dataset selection section (removed duplicate heading)
        
        # Single-column layout for dataset selection
        left_col, right_col = st.columns(2)
        
        with left_col:
            # Simple dataset selection with clean filenames
            st.write("**Select datasets to view:**")
            selected_files = []
            
            # Filter available datasets by selected space
            space_filtered_datasets = {}
            for filename, df in self.datasets.items():
                if 'Space' in df.columns and selected_space in df['Space'].values:
                    space_filtered_datasets[filename] = df
            
            # Get smart defaults for this specific space
            smart_defaults = get_smart_defaults(selected_space)
            
            # Simple list of datasets with clean names
            for filename in list(space_filtered_datasets.keys()):
                friendly_name = self.dataset_friendly_names.get(filename, filename)
                # Remove space prefix from friendly name since space is already selected
                display_name = friendly_name.replace(f"{selected_space} - ", "")
                # Check if this file should be selected by default
                default_checked = filename in smart_defaults
                if st.checkbox(display_name, value=default_checked, key=f"dataset_{filename}"):
                    selected_files.append(filename)
        
        if not selected_files:
            st.warning(f"Please select at least one dataset for {selected_space}")
            return
        
        # Combine selected datasets (they're already filtered by space)
        combined_df = pd.concat([
            self.datasets[filename] for filename in selected_files
        ], ignore_index=True)
        
        with right_col:
            # Download button in the right column below space selector
            st.write("")  # Add some spacing
            st.write("")  # Add more spacing for download button
            
            # We'll add the download button here after we create the display_df
            download_placeholder = st.empty()
        
        st.write("") # Add some spacing
        
        # Search functionality - Full width
        search_term = st.text_input(
            "**Search in data:**", 
            "", 
            help="Search across all data fields",
            placeholder="Enter search term..."
        )
        if search_term:
            # Search across all string columns
            string_cols = combined_df.select_dtypes(include=['object']).columns
            mask = combined_df[string_cols].astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            combined_df = combined_df[mask]
        
        # Display the filtered table
        
        # Add column selection
        available_columns = [col for col in combined_df.columns if col not in ['Source File', 'Dataset Type', 'Space', 'Timestamp']]
        selected_columns = st.multiselect(
            "Select columns to display:",
            options=available_columns,
            default=available_columns[:10] if len(available_columns) > 10 else available_columns
        )
        
        if selected_columns:
            # Reorder columns: Space first, then selected columns, then Dataset Type, then Source File last
            column_order = ['Space'] + selected_columns + ['Dataset Type', 'Source File']
            display_df = combined_df[column_order]
            
            # Simple dataframe without custom alignment
            column_config = {}
            
            st.dataframe(
                display_df, 
                use_container_width=True,
                height=len(display_df) * 35 + 38,  # Dynamic height: ~35px per row + header
                column_config=column_config
            )
            
            # Removed duplicate download button - keeping the one in header
        else:
            st.warning("Please select at least one column to display")
    
    def render_data_visualization(self):
        """Render quick data visualizations"""
        if not self.datasets:
            return
            
        st.subheader("Quick Data Insights")
        
        # Dataset distribution pie chart
        dataset_counts = {}
        for df in self.datasets.values():
            if 'dataset_type' in df.columns:
                for dtype in df['dataset_type'].unique():
                    dataset_counts[dtype] = dataset_counts.get(dtype, 0) + len(df[df['dataset_type'] == dtype])
        
        if dataset_counts:
            fig = px.pie(
                values=list(dataset_counts.values()),
                names=list(dataset_counts.keys()),
                title="Data Distribution by Type"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Space distribution
        space_counts = {}
        for df in self.datasets.values():
            if 'space' in df.columns:
                for space in df['space'].unique():
                    space_counts[space] = space_counts.get(space, 0) + len(df[df['space'] == space])
        
        if space_counts:
            fig = px.bar(
                x=list(space_counts.keys()),
                y=list(space_counts.values()),
                title="Data Points by Space",
                labels={'x': 'Space', 'y': 'Number of Data Points'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render(self, selected_space=None):
        """Main render method for the Data Explorer component"""
        
        # Two-column header layout matching other pages
        header_col1, header_col2 = st.columns([1, 1])
        
        with header_col1:
            st.info("**📊 Select datasets to view:**")
        
        with header_col2:
            # Download CSV button (replacing panel count controls)
            
            # Get all CSV files in the data directory
            data_path = Path('data/generated')
            csv_files = list(data_path.glob('*.csv'))
            
            if csv_files:
                # Create a combined CSV for download
                combined_data = {}
                for csv_file in csv_files:
                    try:
                        df = pd.read_csv(csv_file)
                        sheet_name = csv_file.stem.replace('250728-', '').replace('-', '_')
                        combined_data[sheet_name] = df
                    except Exception as e:
                        st.error(f"Error reading {csv_file.name}: {e}")
                
                if combined_data:
                    # Create download button for combined CSV
                    from io import StringIO
                    combined_csv = StringIO()
                    first_sheet = True
                    for sheet_name, df in combined_data.items():
                        if not first_sheet:
                            combined_csv.write('\n\n')
                        combined_csv.write(f"=== {sheet_name} ===\n")
                        df.to_csv(combined_csv, index=False)
                        first_sheet = False
                    
                    st.download_button(
                        label="Download filtered data as CSV",
                        data=combined_csv.getvalue(),
                        file_name=f"cbc_acoustic_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        help="Download all analysis data as a single CSV file",
                        use_container_width=True
                    )
            else:
                st.warning("No CSV files found in data/generated directory")
        
        # Removed horizontal divider for cleaner layout
        
        # Load data
        if not self.datasets:
            with st.spinner("Loading datasets..."):
                if not self.load_all_datasets():
                    st.error("Failed to load datasets")
                    return
        
        # Main data table interface
        self.render_data_table(selected_space)

# Convenience function for integration
def render_data_explorer(selected_space=None):
    """Convenience function to render the Data Explorer component"""
    explorer = DataExplorer()
    explorer.render(selected_space)