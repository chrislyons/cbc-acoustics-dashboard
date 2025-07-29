# Quick Start - Run Dashboard on Host Machine

Since DCC is in a Docker container without port mapping, you need to run the dashboard on your host machine.

## Option 1: Use the existing virtual environment (if it was created earlier)
```bash
cd /Users/chrislyons/Documents/CL/dev/std8/cbc-interactive-dashboard
./cbc-dashboard-env/bin/streamlit run web_acoustic_dashboard.py
```

## Option 2: Install and run directly (simplest)
```bash
cd /Users/chrislyons/Documents/CL/dev/std8/cbc-interactive-dashboard
pip3 install --user streamlit plotly pandas numpy
python3 -m streamlit run web_acoustic_dashboard.py
```

## Option 3: Create a new virtual environment
```bash
cd /Users/chrislyons/Documents/CL/dev/std8/cbc-interactive-dashboard
python3 -m venv myenv
./myenv/bin/pip install streamlit plotly pandas numpy
./myenv/bin/streamlit run web_acoustic_dashboard.py
```

The dashboard will open at http://localhost:8501

## What I Fixed:
1. Removed excessive CSS !important declarations that were causing display issues
2. The dashboard is now ready to run, you just need to execute it from your host machine (not inside Docker)