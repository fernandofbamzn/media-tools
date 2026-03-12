#!/usr/bin/env bash

set -e

echo "Inicializando repositorio git..."

if [ ! -d ".git" ]; then
    git init
fi

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.pyc

# Virtualenv
.venv/

# Editor
.vscode/
.idea/

# Logs
*.log

# OS
.DS_Store
EOF

git add .

git commit -m "Initial commit: base CLI architecture, dependency system, navigation and audit services"

echo "Repositorio git inicializado correctamente"
