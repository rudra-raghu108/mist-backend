export interface ChatMessage {
  id: string;
  userId: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    confidence?: number;
    source?: string;
    trainingData?: Array<{
      question: string;
      answer: string;
      confidence: number;
    }>;
    tokens?: number;
    processingTime?: number;
  };
}

export interface ChatSession {
  id: string;
  userId: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
  isActive: boolean;
  tags?: string[];
  summary?: string;
}

export interface ChatRequest {
  message: string;
  sessionId?: string;
  context?: string;
  options?: {
    includeTrainingData?: boolean;
    maxTokens?: number;
    temperature?: number;
  };
}

export interface ChatResponse {
  success: boolean;
  message: ChatMessage;
  sessionId: string;
  suggestions?: string[];
  metadata?: {
    confidence: number;
    source: string;
    processingTime: number;
    tokensUsed: number;
  };
}

export interface ChatHistory {
  sessions: ChatSession[];
  totalSessions: number;
  totalMessages: number;
  averageMessagesPerSession: number;
}

export interface ChatAnalytics {
  totalChats: number;
  totalMessages: number;
  averageResponseTime: number;
  mostCommonTopics: Array<{
    topic: string;
    count: number;
  }>;
  userSatisfaction: number;
  trainingDataQuality: number;
}

export interface ChatExport {
  sessionId: string;
  title: string;
  messages: Array<{
    role: string;
    content: string;
    timestamp: string;
  }>;
  exportDate: string;
  format: 'txt' | 'json' | 'pdf';
}


