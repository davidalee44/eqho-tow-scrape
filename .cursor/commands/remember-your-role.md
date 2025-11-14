#!/bin/bash

# save as: scripts/verify-workspace.sh

echo "🔍 Verifying Workspace Configuration"
echo "===================================="

# Check current directory

echo -n "Current directory: "
pwd

# Check if in correct location

if [[ $(basename "$(pwd)") == "eqho-audio-pii-redaction" ]]; then
    echo "✅ Correct working directory"
else
    echo "❌ Wrong directory - should be in eqho-audio-pii-redaction"
    exit 1
fi

# Check key files exist

for file in "Makefile" "docker-compose.yml" "backend/pyproject.toml" "frontend/package.json"; do
    if [[ -f "$file" ]]; then
        echo "✅ Found: $file"
    else
        echo "❌ Missing: $file"
    fi
done

# Test make command

if make help >/dev/null 2>&1; then
    echo "✅ Make commands working"
else
    echo "❌ Make commands not working"
fi

echo ""
echo "Setup verification complete!"
