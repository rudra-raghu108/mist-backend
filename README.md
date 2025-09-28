# MIST AI Backend

A powerful backend for MIST AI - Personal AI Assistant with Training Capabilities for SRM University students.

## 🚀 Features

- **Personal AI Training**: Each user can train their own AI with custom responses and training data
- **Intelligent Query Processing**: Uses OpenAI API + local training data for personalized responses
- **User Authentication**: Secure JWT-based authentication system
- **Real-time Chat**: Socket.IO integration for live chat experiences
- **AI Model Training**: Continuous learning from user interactions
- **Custom Response System**: Users can define trigger-response pairs
- **Analytics & Insights**: Track AI performance and user satisfaction
- **Scalable Architecture**: Built with TypeScript, Express, and MongoDB

## 🛠️ Tech Stack

- **Runtime**: Node.js 18+
- **Framework**: Express.js
- **Language**: TypeScript
- **Database**: MongoDB with Mongoose
- **Authentication**: JWT + bcrypt
- **AI Integration**: OpenAI API + Natural Language Processing
- **Real-time**: Socket.IO
- **Validation**: Express-validator
- **Logging**: Winston
- **Rate Limiting**: Express-rate-limit

## 📋 Prerequisites

- Node.js 18+ installed
- MongoDB instance running
- OpenAI API key
- Git

## 🚀 Quick Start

### 1. Clone and Install

```bash
# Navigate to backend directory
cd backend

# Install dependencies
npm install

# Copy environment file
cp env.example .env
```

### 2. Environment Configuration

Edit `.env` file with your configuration:

```env
# Server Configuration
PORT=5000
NODE_ENV=development

# Database Configuration
MONGODB_URI=mongodb://localhost:27017/mist-ai

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-here
JWT_EXPIRES_IN=7d

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000

# CORS Configuration
CORS_ORIGIN=http://localhost:3000
```

### 3. Start Development Server

```bash
# Development mode with hot reload
npm run dev

# Build and start production
npm run build
npm start
```

## 📚 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user profile
- `PUT /api/auth/profile` - Update user profile
- `POST /api/auth/change-password` - Change password

### AI & Chat
- `POST /api/ai/chat` - Send message to AI
- `GET /api/ai/history` - Get chat history
- `POST /api/ai/feedback` - Provide feedback on AI responses

### Training
- `POST /api/training/data` - Add training data
- `GET /api/training/data` - Get training data
- `POST /api/training/train` - Train AI model
- `POST /api/training/custom-response` - Add custom response
- `GET /api/training/analytics` - Get training analytics

### User Management
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update user profile
- `GET /api/user/usage` - Get usage statistics
- `DELETE /api/user/account` - Delete account

### Admin (Admin only)
- `GET /api/admin/users` - Get all users
- `GET /api/admin/analytics` - Get system analytics
- `POST /api/admin/user/:id/activate` - Activate user
- `POST /api/admin/user/:id/deactivate` - Deactivate user

## 🧠 AI Training System

### How It Works

1. **Custom Responses**: Users can define trigger words/phrases that automatically generate specific responses
2. **Training Data**: The AI learns from user interactions and feedback
3. **Similarity Matching**: Uses TF-IDF and cosine similarity to find relevant training examples
4. **OpenAI Integration**: Falls back to OpenAI for complex queries
5. **Continuous Learning**: AI improves over time with more training data

### Training Your AI

```typescript
// Add custom response
POST /api/training/custom-response
{
  "trigger": "admission deadline",
  "response": "Admission deadlines for SRM are usually in April-May. Check the official website for current dates.",
  "priority": 8
}

// Add training data
POST /api/training/data
{
  "question": "What are the hostel fees?",
  "answer": "Hostel fees range from ₹80,000 to ₹1,50,000 per year depending on room type.",
  "confidence": 0.9
}

// Train model
POST /api/training/train
```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt with salt rounds
- **Rate Limiting**: Prevent abuse and DDoS attacks
- **Input Validation**: Comprehensive request validation
- **CORS Protection**: Configurable cross-origin settings
- **Helmet Security**: Security headers and protection

## 📊 Monitoring & Logging

- **Winston Logger**: Structured logging with multiple levels
- **Request Logging**: Morgan HTTP request logging
- **Error Tracking**: Comprehensive error handling and logging
- **Performance Metrics**: Response time and usage tracking

## 🚀 Deployment

### Docker (Recommended)

```bash
# Build Docker image
docker build -t mist-ai-backend .

# Run container
docker run -p 5000:5000 --env-file .env mist-ai-backend
```

### Manual Deployment

```bash
# Build for production
npm run build

# Start production server
npm start

# Use PM2 for process management
pm2 start dist/index.js --name "mist-ai-backend"
```

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

## 📁 Project Structure

```
backend/
├── src/
│   ├── config/          # Configuration files
│   ├── controllers/     # Route controllers
│   ├── middleware/      # Custom middleware
│   ├── models/          # Database models
│   ├── routes/          # API routes
│   ├── services/        # Business logic
│   ├── types/           # TypeScript types
│   ├── utils/           # Utility functions
│   └── index.ts         # Main server file
├── logs/                # Log files
├── uploads/             # File uploads
├── package.json         # Dependencies
├── tsconfig.json        # TypeScript config
└── README.md            # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation
- Review the logs for debugging

## 🔮 Future Enhancements

- **Vector Database Integration**: For better semantic search
- **Multi-language Support**: Internationalization
- **Advanced Analytics**: Machine learning insights
- **API Versioning**: Backward compatibility
- **Webhook Support**: External integrations
- **Mobile App**: React Native companion app

---

**Built with ❤️ for the SRM University Community**


