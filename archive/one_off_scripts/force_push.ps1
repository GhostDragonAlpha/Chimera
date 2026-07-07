# Force Push Script for Chimera Project
$ErrorActionPreference = "Stop"
Set-Location -Path "e:\PythonChimera"

# Remove existing .git if corrupted
if (Test-Path ".git") {
    Remove-Item -Recurse -Force ".git"
}

# Initialize git repository
git init -b master

# Configure git user
git config --local user.name "GhostDragonAlpha"
git config --local user.email "ghostdragonalpha@github.com"

# Add remote origin
git remote add origin https://github.com/GhostDragonAlpha/Chimera.git

# Add all files and commit
git add .
git commit -m "Force push overwrite: complete project state"

# Fetch from remote to ensure we have latest refs
git fetch --all || true

# Force push to master branch
git push --force --set-upstream origin master

Write-Output "Force push completed successfully."
