#!/bin/bash
# =============================================================================
# NABIH Platform Shutdown Script
# Gracefully stops all services to save resources
# =============================================================================

echo "=============================================="
echo "   نـبـيـه | NABIH Platform Shutdown"
echo "=============================================="
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔄 Stopping services...${NC}"
echo ""

# Stop Backend
echo "Stopping Backend API..."
sudo systemctl stop nabeeh_api
echo -e "${GREEN}✅ Backend stopped${NC}"

# Note: We keep Nginx, MongoDB, and Ollama running
# Ollama keeps models in memory for faster restart

echo ""
echo "=============================================="
echo -e "${GREEN}   NABIH Platform Stopped${NC}"
echo "=============================================="
echo ""
echo "ℹ️  Note: MongoDB, Nginx, and Ollama are still running"
echo "    to enable faster restart."
echo ""
echo "To completely stop everything:"
echo "    sudo systemctl stop ollama mongod nginx"
echo ""
echo "To restart NABIH:"
echo "    ./start_nabih.sh"
echo ""
