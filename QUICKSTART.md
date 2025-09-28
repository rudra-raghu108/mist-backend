# MIST AI Backend - Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Install Dependencies
```bash
npm install
```

### 2. Set Up Environment
```bash
# Copy environment template
cp env.example .env

# Edit .env with your settings:
# - OpenAI API key (get from https://platform.openai.com/)
# - JWT secret (any random string)
# - MongoDB URI (use localhost for development)
```

### 3. Start Development Server
```bash
npm run dev
```

## 🎯 What's Working Now

✅ **Basic Express Server** - Running on port 5000  
✅ **User Authentication** - Register, login, logout  
✅ **Database Models** - User model with AI training data  
✅ **API Routes** - All endpoints are set up  
✅ **Middleware** - Auth, validation, error handling  
✅ **Health Check** - Visit http://localhost:5000/health  

## 🔧 What's Coming Next

🔄 **AI Integration** - OpenAI API integration  
🔄 **Natural Language Processing** - Advanced similarity matching  
🔄 **Real-time Chat** - Socket.IO implementation  
🔄 **AI Training** - Personal model training  

## 🧪 Test the API

### Health Check
```bash
curl http://localhost:5000/health
```

### Register User
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "Password123",
    "campus": "Kattankulathur (KTR)",
    "focus": "General"
  }'
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Change port in .env file
PORT=5001
```

### MongoDB Connection Issues
```bash
# Make sure MongoDB is running
# For local development, install MongoDB Community Edition
# Or use Docker: docker run -d -p 27017:27017 mongo:7.0
```

### Package Installation Errors
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 📁 Project Structure

```
backend/
├── src/
│   ├── config/          # Database configuration
│   ├── middleware/      # Auth & error handling
│   ├── models/          # Database models
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic
│   ├── types/           # TypeScript types
│   ├── utils/           # Logging utilities
│   └── index.ts         # Main server file
├── package.json         # Dependencies
├── tsconfig.json        # TypeScript config
├── env.example          # Environment template
└── README.md            # Full documentation
```

## 🎉 You're Ready!

The backend is now running and ready for:
- User registration and authentication
- Basic API structure
- Database operations
- Future AI integration

Visit http://localhost:5000/health to confirm everything is working!


