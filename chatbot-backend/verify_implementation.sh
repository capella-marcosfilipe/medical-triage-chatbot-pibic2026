#!/usr/bin/env bash

echo "=================================="
echo "🔍 Verification Script for Medical Triage Chatbot API"
echo "=================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "\n${YELLOW}1. Checking Python version...${NC}"
python --version
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Python is installed${NC}"
else
    echo -e "${RED}✗ Python is not installed${NC}"
    exit 1
fi

# Check if all required files exist
echo -e "\n${YELLOW}2. Checking required files...${NC}"
FILES=(
    "main.py"
    "requirements.txt"
    ".env.example"
    "README.md"
    "API.md"
    "DEPLOYMENT.md"
    "Dockerfile"
    "docker-compose.yml"
    "Procfile"
    "app/core/config.py"
    "app/models/schemas.py"
    "app/services/session_manager.py"
    "app/services/gemini_service.py"
    "app/services/smartwatch_simulator.py"
    "app/api/v1/endpoints.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file - MISSING"
        exit 1
    fi
done

# Check Python syntax
echo -e "\n${YELLOW}3. Checking Python syntax...${NC}"
python -m py_compile main.py app/core/config.py app/models/schemas.py app/services/*.py app/api/v1/endpoints.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All Python files have valid syntax${NC}"
else
    echo -e "${RED}✗ Syntax errors found${NC}"
    exit 1
fi

# Check dependencies
echo -e "\n${YELLOW}4. Checking dependencies installation...${NC}"
MISSING_DEPS=0
for dep in "fastapi" "uvicorn" "pydantic" "google-generativeai"; do
    if pip list | grep -q "^$dep "; then
        echo -e "${GREEN}✓${NC} $dep"
    else
        echo -e "${RED}✗${NC} $dep - MISSING"
        MISSING_DEPS=1
    fi
done
if [ $MISSING_DEPS -eq 1 ]; then
    echo -e "${RED}✗ Some dependencies are missing. Run: pip install -r requirements.txt${NC}"
    exit 1
fi

# Check project structure
echo -e "\n${YELLOW}5. Checking project structure...${NC}"
DIRS=(
    "app"
    "app/api"
    "app/api/v1"
    "app/core"
    "app/models"
    "app/services"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir/"
    else
        echo -e "${RED}✗${NC} $dir/ - MISSING"
        exit 1
    fi
done

echo -e "\n${GREEN}=================================="
echo "✅ All verification checks passed!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and add your GOOGLE_API_KEY"
echo "2. Run: python main.py"
echo "3. Open: http://localhost:8001/docs"
echo "4. Test with: python test_api.py"
echo ""
