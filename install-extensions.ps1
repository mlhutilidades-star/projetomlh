# Script de instalação de extensões VS Code
# Execute este arquivo no PowerShell ou copie os comandos abaixo

# Python Development
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.debugpy

# Code Quality & Formatting
code --install-extension ms-python.black-formatter
code --install-extension charliermarsh.ruff
code --install-extension ms-python.isort

# AI & Productivity
code --install-extension github.copilot
code --install-extension github.copilot-chat

# Git & GitHub
code --install-extension github.vscode-pull-request-github
code --install-extension eamodio.gitlens

# Streamlit
code --install-extension quarto.quarto

# Data Science & Notebooks
code --install-extension ms-toolsai.jupyter
code --install-extension ms-toolsai.jupyter-keymap
code --install-extension ms-toolsai.jupyter-renderers

# Database
code --install-extension mtxr.sqltools
code --install-extension mtxr.sqltools-driver-sqlite

# API Development & Testing
code --install-extension humao.rest-client
code --install-extension rangav.vscode-thunder-client

# YAML & Config Files
code --install-extension redhat.vscode-yaml

# Markdown & Documentation
code --install-extension yzhang.markdown-all-in-one
code --install-extension bierner.markdown-mermaid

# Environment & Dependencies
code --install-extension donjayamanne.python-environment-manager

# Code Navigation & IntelliSense
code --install-extension visualstudioexptteam.vscodeintellicode
code --install-extension visualstudioexptteam.intellicode-api-usage-examples

# File Icons
code --install-extension vscode-icons-team.vscode-icons

# Terminal
code --install-extension ms-vscode.powershell

# XML/HTML
code --install-extension redhat.vscode-xml

# Path Autocomplete
code --install-extension christian-kohler.path-intellisense

# Bracket Colorizer
code --install-extension coenraads.bracket-pair-colorizer-2

# Error Lens
code --install-extension usernamehw.errorlens

# Better Comments
code --install-extension aaron-bond.better-comments

# TODO Highlight
code --install-extension wayou.vscode-todo-highlight

# Live Share
code --install-extension ms-vsliveshare.vsliveshare

Write-Host "`n✅ Instalação completa! Reinicie o VS Code para ativar todas as extensões." -ForegroundColor Green
