#!/bin/bash
# =============================================================================
# NABIH Platform Startup Script
# Automatically starts all services and loads AI models
# =============================================================================

echo "=============================================="
echo "   نـبـيـه | NABIH Platform Startup"
echo "   Clinical Documentation Improvement System"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service status
check_service() {
    if systemctl is-active --quiet $1; then
        echo -e "${GREEN}✅ $1 is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 is not running${NC}"
        return 1
    fi
}

# Function to start service if not running
start_service() {
    if ! systemctl is-active --quiet $1; then
        echo -e "${YELLOW}🔄 Starting $1...${NC}"
        sudo systemctl start $1
        sleep 2
    fi
    check_service $1
}

echo "📍 Step 1: Starting Core Services..."
echo "------------------------------------"

# Start MongoDB
start_service mongod

# Start Ollama
start_service ollama

# Wait for Ollama to be ready
echo ""
echo "📍 Step 2: Checking AI Models..."
echo "--------------------------------"

# Check if models are loaded
MODELS=$(ollama list 2>/dev/null)

if echo "$MODELS" | grep -q "qwen2.5:7b"; then
    echo -e "${GREEN}✅ Chat model (qwen2.5:7b) is available${NC}"
else
    echo -e "${YELLOW}🔄 Loading chat model (qwen2.5:7b)...${NC}"
    ollama pull qwen2.5:7b &
fi

if echo "$MODELS" | grep -q "qwen2.5:32b"; then
    echo -e "${GREEN}✅ Analysis model (qwen2.5:32b) is available${NC}"
else
    echo -e "${YELLOW}🔄 Loading analysis model (qwen2.5:32b)...${NC}"
    echo -e "${YELLOW}   This may take a while (19GB)...${NC}"
    ollama pull qwen2.5:32b &
fi

echo ""
echo "📍 Step 3: Starting Backend API..."
echo "----------------------------------"

# Kill any existing uvicorn processes on port 8001
pkill -f 'uvicorn.*8001' 2>/dev/null || true
sleep 1

# Start Backend
start_service nabeeh_api

echo ""
echo "📍 Step 4: Starting Web Server..."
echo "---------------------------------"

# Start Nginx
start_service nginx

echo ""
echo "📍 Step 5: Verifying Services..."
echo "--------------------------------"

# Test API
API_RESPONSE=$(curl -s http://localhost:8001/api/ 2>/dev/null)
if echo "$API_RESPONSE" | grep -q "active"; then
    echo -e "${GREEN}✅ API is responding correctly${NC}"
else
    echo -e "${RED}❌ API is not responding${NC}"
fi

# Test Frontend
FRONTEND_RESPONSE=$(curl -s http://localhost/ 2>/dev/null | head -1)
if echo "$FRONTEND_RESPONSE" | grep -q "html"; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "${RED}❌ Frontend is not accessible${NC}"
fi

echo ""
echo "=============================================="
echo -e "${GREEN}   🎉 NABIH Platform is Ready!${NC}"
echo "=============================================="
echo ""
echo "🌐 Access the platform at: http://$(hostname -I | awk '{print $1}')"
echo ""
echo "📊 Service Status:"
echo "   - MongoDB:  $(systemctl is-active mongod)"
echo "   - Ollama:   $(systemctl is-active ollama)"
echo "   - Backend:  $(systemctl is-active nabeeh_api)"
echo "   - Nginx:    $(systemctl is-active nginx)"
echo ""
echo "📝 Logs:"
echo "   - Backend: sudo journalctl -u nabeeh_api -f"
echo "   - Nginx:   sudo tail -f /var/log/nginx/error.log"
echo ""
