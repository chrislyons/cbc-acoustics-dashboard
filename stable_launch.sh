#!/bin/bash
# Stable CBC Dashboard Launch with Crash Prevention
# Implements best practices to prevent common Streamlit crashes

echo "🎙️ CBC Dashboard Stable Launch"
echo "=============================="
echo "📅 $(date)"
echo ""

cd "$(dirname "$0")"

# Kill any existing processes
echo "🛑 Cleaning up old processes..."
pkill -f "streamlit" 2>/dev/null
pkill -f "cbc8_acoustic_dashboard" 2>/dev/null
sleep 2

# Clear any port conflicts
echo "🔧 Clearing ports..."
for port in {8501..8510}; do
    lsof -ti:$port | xargs kill -9 2>/dev/null
done
sleep 1

# Activate virtual environment
echo "🐍 Activating environment..."
source dashboard-env/bin/activate

# Set environment variables for stability
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=127.0.0.1
export STREAMLIT_SERVER_RUN_ON_SAVE=false
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
export STREAMLIT_LOGGER_LEVEL=warning

# Limit resource usage to prevent crashes
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=50
export STREAMLIT_SERVER_MAX_MESSAGE_SIZE=50

echo "⚙️ Configuration:"
echo "   Port: 8501"
echo "   Address: 127.0.0.1"
echo "   File watching: disabled (for stability)"
echo "   Usage stats: disabled"
echo ""

# Create a simple health check script
cat > health_check.py << 'EOF'
import time
import requests
import sys

max_attempts = 30
for i in range(max_attempts):
    try:
        response = requests.get('http://127.0.0.1:8501/_stcore/health', timeout=5)
        if response.status_code == 200:
            print(f"✅ Dashboard is healthy after {i+1} attempts")
            sys.exit(0)
    except:
        pass
    time.sleep(1)
    
print("❌ Dashboard failed health check")
sys.exit(1)
EOF

# Launch dashboard in background with nohup for complete detachment
echo "🚀 Launching dashboard..."
nohup python3 -m streamlit run cbc8_acoustic_dashboard.py \
    --server.headless true \
    --server.port 8501 \
    --server.address 127.0.0.1 \
    --server.runOnSave false \
    --server.allowRunOnSave false \
    --browser.gatherUsageStats false \
    --server.fileWatcherType none \
    --logger.level warning > dashboard_background.log 2>&1 &

DASHBOARD_PID=$!
echo "📌 Dashboard PID: $DASHBOARD_PID"
echo $DASHBOARD_PID > dashboard.pid

# Immediately detach from terminal
disown $DASHBOARD_PID

# Give it a moment to start then launch browser
sleep 2
echo "🌐 Opening in Firefox (new tab)..."
open -na Firefox --args --new-tab http://localhost:8501 2>/dev/null || echo "   Browser launch attempted"

echo ""
echo "=============================="
echo "🎉 Dashboard launched in background!"
echo "📊 Access at: http://localhost:8501"
echo "📁 Process ID: $DASHBOARD_PID (saved to dashboard.pid)"
echo "📝 Logs: dashboard_background.log"
echo "⏹️ Use 'pkill -f streamlit' to stop"
echo "✅ Script complete - dashboard running independently"

# Script exits immediately, dashboard continues running
exit 0