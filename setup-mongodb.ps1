# ============================================
# MONGODB SETUP SCRIPT FOR WINDOWS
# ============================================
# This script helps you set up MongoDB on Windows
# ============================================

Write-Host "🚀 MongoDB Setup for SRM Guide Bot" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check if MongoDB is already installed
Write-Host "`n1️⃣ Checking MongoDB installation..." -ForegroundColor Yellow
try {
    $mongodVersion = mongod --version 2>$null
    if ($mongodVersion) {
        Write-Host "✅ MongoDB is already installed!" -ForegroundColor Green
        Write-Host $mongodVersion -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ MongoDB not found. Let's install it!" -ForegroundColor Red
}

# Check if MongoDB service is running
Write-Host "`n2️⃣ Checking MongoDB service status..." -ForegroundColor Yellow
$mongodbService = Get-Service -Name "MongoDB" -ErrorAction SilentlyContinue
if ($mongodbService) {
    if ($mongodbService.Status -eq "Running") {
        Write-Host "✅ MongoDB service is running!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ MongoDB service exists but not running. Starting..." -ForegroundColor Yellow
        Start-Service -Name "MongoDB"
        Write-Host "✅ MongoDB service started!" -ForegroundColor Green
    }
} else {
    Write-Host "❌ MongoDB service not found. You may need to install MongoDB first." -ForegroundColor Red
}

# Check if data directory exists
Write-Host "`n3️⃣ Checking MongoDB data directory..." -ForegroundColor Yellow
$dataDir = "C:\data\db"
if (Test-Path $dataDir) {
    Write-Host "✅ Data directory exists: $dataDir" -ForegroundColor Green
} else {
    Write-Host "⚠️ Data directory doesn't exist. Creating..." -ForegroundColor Yellow
    try {
        New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
        Write-Host "✅ Data directory created: $dataDir" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to create data directory. You may need admin rights." -ForegroundColor Red
    }
}

# Test MongoDB connection
Write-Host "`n4️⃣ Testing MongoDB connection..." -ForegroundColor Yellow
try {
    $testConnection = python -c "
import pymongo
try:
    client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✅ MongoDB connection successful!')
    print(f'Server version: {client.server_info()[\"version\"]}')
    client.close()
except Exception as e:
    print(f'❌ MongoDB connection failed: {e}')
    exit(1)
" 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ MongoDB connection test passed!" -ForegroundColor Green
    } else {
        Write-Host "❌ MongoDB connection test failed!" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Could not test MongoDB connection. Make sure Python and pymongo are installed." -ForegroundColor Red
}

# Install Python dependencies
Write-Host "`n5️⃣ Installing Python MongoDB dependencies..." -ForegroundColor Yellow
try {
    Write-Host "Installing pymongo..." -ForegroundColor Gray
    pip install pymongo==4.6.1 motor==3.3.2 dnspython==2.6.1
    Write-Host "✅ MongoDB Python packages installed!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install Python packages. Try running manually:" -ForegroundColor Red
    Write-Host "pip install pymongo==4.6.1 motor==3.3.2 dnspython==2.6.1" -ForegroundColor Yellow
}

# Setup environment file
Write-Host "`n6️⃣ Setting up environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "⚠️ .env file already exists. Backing up..." -ForegroundColor Yellow
    Copy-Item ".env" ".env.backup"
}

if (Test-Path "env-mongodb.txt") {
    Copy-Item "env-mongodb.txt" ".env"
    Write-Host "✅ Environment file created from env-mongodb.txt" -ForegroundColor Green
    Write-Host "📝 Edit .env file with your actual API keys and settings" -ForegroundColor Cyan
} else {
    Write-Host "❌ env-mongodb.txt not found. Creating basic .env..." -ForegroundColor Red
    @"
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=srm_guide_bot
MONGO_USERNAME=
MONGO_PASSWORD=

# OpenAI (Required)
OPENAI_API_KEY=your-openai-api-key-here

# JWT (Required)
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Basic .env file created" -ForegroundColor Green
}

# Final instructions
Write-Host "`n🎉 MongoDB Setup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your OpenAI API key" -ForegroundColor White
Write-Host "2. Make sure MongoDB service is running" -ForegroundColor White
Write-Host "3. Test your backend: python main.py" -ForegroundColor White
Write-Host "`n🔧 If MongoDB is not working:" -ForegroundColor Red
Write-Host "1. Download MongoDB from: https://www.mongodb.com/try/download/community" -ForegroundColor White
Write-Host "2. Install as Windows Service" -ForegroundColor White
Write-Host "3. Restart this script" -ForegroundColor White
Write-Host "`n📚 For help: https://docs.mongodb.com/manual/installation/" -ForegroundColor Cyan

Write-Host "`nPress any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")



