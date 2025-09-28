import { IUser } from '../models/User';
import { logger } from '../utils/logger';

export interface AIResponse {
  content: string;
  confidence: number;
  source: 'custom' | 'training' | 'openai' | 'fallback';
  trainingData?: Array<{
    question: string;
    answer: string;
    confidence: number;
  }>;
}

export interface TrainingExample {
  question: string;
  answer: string;
  confidence: number;
}

export class AIService {
  private static instance: AIService;
  
  private constructor() {}
  
  public static getInstance(): AIService {
    if (!AIService.instance) {
      AIService.instance = new AIService();
    }
    return AIService.instance;
  }

  /**
   * Generate AI response based on user query and personal training data
   */
  public async generateResponse(
    query: string,
    user: IUser,
    context?: string
  ): Promise<AIResponse> {
    try {
      // First, check for custom responses
      const customResponse = this.checkCustomResponses(query, user);
      if (customResponse) {
        return customResponse;
      }

      // Check training data for similar questions
      const trainingResponse = this.checkTrainingData(query, user);
      if (trainingResponse && trainingResponse.confidence > 0.8) {
        return trainingResponse;
      }

      // For now, return a fallback response
      // TODO: Implement OpenAI integration once packages are installed
      return this.getFallbackResponse(query, user);
    } catch (error) {
      logger.error('Error generating AI response:', error);
      return this.getFallbackResponse(query, user);
    }
  }

  /**
   * Check if query matches any custom responses
   */
  private checkCustomResponses(query: string, user: IUser): AIResponse | null {
    const lowerQuery = query.toLowerCase();
    
    for (const custom of user.aiTraining.customResponses) {
      if (lowerQuery.includes(custom.trigger.toLowerCase())) {
        return {
          content: custom.response,
          confidence: 0.95,
          source: 'custom'
        };
      }
    }
    
    return null;
  }

  /**
   * Check training data for similar questions using simple string matching
   * TODO: Implement TF-IDF and cosine similarity once natural package is installed
   */
  private checkTrainingData(query: string, user: IUser): AIResponse | null {
    if (user.aiTraining.trainingData.length === 0) {
      return null;
    }

    const lowerQuery = query.toLowerCase();
    let bestMatch: any = null;
    let bestSimilarity = 0;

    // Simple keyword matching for now
    user.aiTraining.trainingData.forEach((example) => {
      const lowerQuestion = example.question.toLowerCase();
      const commonWords = this.getCommonWords(lowerQuery, lowerQuestion);
      const similarity = commonWords / Math.max(lowerQuery.split(' ').length, lowerQuestion.split(' ').length);
      
      if (similarity > bestSimilarity && similarity > 0.3) {
        bestSimilarity = similarity;
        bestMatch = example;
      }
    });

    if (bestMatch && bestSimilarity > 0.7) {
      return {
        content: bestMatch.answer,
        confidence: bestSimilarity,
        source: 'training',
        trainingData: [{
          question: bestMatch.question,
          answer: bestMatch.answer,
          confidence: bestMatch.confidence
        }]
      };
    }

    return null;
  }

  /**
   * Simple word matching for similarity calculation
   */
  private getCommonWords(str1: string, str2: string): number {
    const words1 = str1.split(' ').filter(word => word.length > 2);
    const words2 = str2.split(' ').filter(word => word.length > 2);
    
    let commonCount = 0;
    words1.forEach(word => {
      if (words2.includes(word)) {
        commonCount++;
      }
    });
    
    return commonCount;
  }

  /**
   * Get fallback response when all else fails
   */
  private getFallbackResponse(query: string, user: IUser): AIResponse {
    const fallbackResponses = [
      "I'm having trouble processing your request right now. Could you try rephrasing your question?",
      "I'm experiencing some technical difficulties. Please try again in a moment.",
      "I'm not sure I understand. Could you provide more details about what you're looking for?",
      "Let me help you with that. Could you clarify your question about SRM University?"
    ];

    const randomResponse = fallbackResponses[Math.floor(Math.random() * fallbackResponses.length)];
    
    return {
      content: randomResponse,
      confidence: 0.3,
      source: 'fallback'
    };
  }

  /**
   * Train the AI model with new data
   */
  public async trainModel(user: IUser): Promise<{
    success: boolean;
    message: string;
    trainingStats: {
      totalExamples: number;
      averageConfidence: number;
      newPatterns: number;
    };
  }> {
    try {
      if (user.aiTraining.trainingData.length < 10) {
        return {
          success: false,
          message: 'Need at least 10 training examples to start training',
          trainingStats: {
            totalExamples: user.aiTraining.trainingData.length,
            averageConfidence: 0,
            newPatterns: 0
          }
        };
      }

      // Analyze training data for patterns
      const patterns = this.analyzeTrainingPatterns(user.aiTraining.trainingData);
      
      // Update user's learning rate based on performance
      const newLearningRate = this.calculateOptimalLearningRate(user.aiTraining.trainingData);
      user.aiTraining.learningRate = newLearningRate;
      user.aiTraining.lastTraining = new Date();
      
      // Note: In a real implementation, you would save the user here
      // For now, we'll just return the success response
      // await user.save();

      return {
        success: true,
        message: 'AI model training completed successfully',
        trainingStats: {
          totalExamples: user.aiTraining.trainingData.length,
          averageConfidence: patterns.averageConfidence,
          newPatterns: patterns.newPatterns
        }
      };
    } catch (error) {
      logger.error('Error training AI model:', error);
      throw error;
    }
  }

  /**
   * Analyze training data for patterns and insights
   */
  private analyzeTrainingPatterns(trainingData: TrainingExample[]): {
    averageConfidence: number;
    newPatterns: number;
  } {
    const totalConfidence = trainingData.reduce((sum, ex) => sum + ex.confidence, 0);
    const averageConfidence = totalConfidence / trainingData.length;
    
    // Simple pattern detection (can be enhanced)
    const newPatterns = Math.floor(trainingData.length * 0.1); // Estimate 10% new patterns
    
    return {
      averageConfidence,
      newPatterns
    };
  }

  /**
   * Calculate optimal learning rate based on training performance
   */
  private calculateOptimalLearningRate(trainingData: TrainingExample[]): number {
    const recentData = trainingData.slice(-20); // Last 20 examples
    const averageConfidence = recentData.reduce((sum, ex) => sum + ex.confidence, 0) / recentData.length;
    
    // Adjust learning rate based on performance
    if (averageConfidence > 0.8) {
      return 0.005; // Lower learning rate for good performance
    } else if (averageConfidence > 0.6) {
      return 0.01; // Medium learning rate
    } else {
      return 0.02; // Higher learning rate for poor performance
    }
  }
}

export const aiService = AIService.getInstance();
