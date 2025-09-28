# ============================================
# OPTIMIZED DEPENDENCY INSTALLATION SCRIPT
# ============================================
# For Windows PowerShell - Optimized for SRM Guide Bot Backend
# ============================================

Write-Host "🚀 SRM Guide Bot - Optimized Dependency Installation" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found. Creating one..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Green
& ".venv\Scripts\Activate.ps1"

# Upgrade pip and build tools
Write-Host "⬆️  Upgrading pip and build tools..." -ForegroundColor Green
python -m pip install --upgrade pip setuptools wheel

# Clean previous installations (optional)
$clean = Read-Host "🧹 Clean previous installations? (y/n) [n]"
if ($clean -eq "y" -or $clean -eq "Y") {
    Write-Host "🧹 Cleaning previous installations..." -ForegroundColor Yellow
    pip uninstall -y -r requirements.txt 2>$null
    pip cache purge
}

# Choose installation type
Write-Host "📦 Choose installation type:" -ForegroundColor Cyan
Write-Host "1. Full installation (with ML dependencies)" -ForegroundColor White
Write-Host "2. Development only (faster, no ML)" -ForegroundColor White
Write-Host "3. Custom selection" -ForegroundColor White

$choice = Read-Host "Enter choice (1-3) [1]"

switch ($choice) {
    "2" {
        Write-Host "🚀 Installing development dependencies..." -ForegroundColor Green
        pip install -r requirements-dev.txt --prefer-binary --no-deps --force-reinstall
        Write-Host "✅ Development dependencies installed!" -ForegroundColor Green
        Write-Host "💡 For ML features, run: pip install torch==2.5.1 transformers==4.46.3" -ForegroundColor Yellow
    }
    "3" {
        Write-Host "🔧 Custom installation..." -ForegroundColor Green
        Write-Host "Available packages:" -ForegroundColor White
        Get-Content requirements.txt | Where-Object { $_ -match "^[a-zA-Z]" -and $_ -notmatch "^#" } | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        
        $packages = Read-Host "Enter package names separated by spaces (or 'all' for everything)"
        if ($packages -eq "all") {
            pip install -r requirements.txt --prefer-binary
        } else {
            pip install $packages --prefer-binary
        }
    }
    default {
        Write-Host "🚀 Installing full dependencies (this may take 10-15 minutes)..." -ForegroundColor Green
        
        # Install in batches for better error handling
        Write-Host "📦 Installing core framework..." -ForegroundColor Green
        pip install fastapi==0.115.4 uvicorn[standard]==0.32.0 pydantic==2.9.2 pydantic-settings==2.6.1
        
        Write-Host "🗄️  Installing database..." -ForegroundColor Green
        pip install sqlalchemy==2.0.36 alembic==1.14.0 asyncpg==0.30.0 psycopg2-binary==2.9.10
        
        Write-Host "🤖 Installing AI & ML..." -ForegroundColor Green
        pip install openai==1.54.4 langchain==0.3.7 langchain-openai==0.2.8 langchain-community==0.3.7 tiktoken==0.8.0
        
        Write-Host "🔥 Installing PyTorch ecosystem..." -ForegroundColor Green
        pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
        
        Write-Host "🔧 Installing remaining packages..." -ForegroundColor Green
        pip install -r requirements.txt --prefer-binary --no-deps
        
        Write-Host "✅ Full installation completed!" -ForegroundColor Green
    }
}

# Verify installation
Write-Host "🔍 Verifying installation..." -ForegroundColor Green
pip list --format=columns

Write-Host "🎉 Installation completed successfully!" -ForegroundColor Green
Write-Host "💡 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Copy pip.conf to your user directory" -ForegroundColor White
Write-Host "   2. Set up environment variables (copy env.example to .env)" -ForegroundColor White
Write-Host "   3. Initialize database: python init_db.py" -ForegroundColor White
Write-Host "   4. Start the server: python main.py" -ForegroundColor White

# Pause to show results
Read-Host "Press Enter to continue..."
