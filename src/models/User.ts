import mongoose, { Document, Schema } from 'mongoose';
import bcrypt from 'bcryptjs';

export interface IUser extends Document {
  email: string;
  password: string;
  name: string;
  profile: {
    avatar?: string;
    campus: string;
    focus: string;
    bio?: string;
    preferences: {
      theme: 'light' | 'dark' | 'auto';
      notifications: boolean;
      aiPersonality: string;
    };
  };
  aiTraining: {
    isEnabled: boolean;
    trainingData: Array<{
      question: string;
      answer: string;
      confidence: number;
      timestamp: Date;
    }>;
    customResponses: Array<{
      trigger: string;
      response: string;
      priority: number;
    }>;
    learningRate: number;
    lastTraining: Date;
  };
  usage: {
    totalChats: number;
    totalTokens: number;
    lastActive: Date;
    plan: 'free' | 'premium' | 'enterprise';
  };
  isActive: boolean;
  isAdmin: boolean;
  createdAt: Date;
  updatedAt: Date;
  comparePassword(candidatePassword: string): Promise<boolean>;
}

const userSchema = new Schema<IUser>({
  email: {
    type: String,
    required: [true, 'Email is required'],
    unique: true,
    lowercase: true,
    trim: true,
    match: [/^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/, 'Please enter a valid email']
  },
  password: {
    type: String,
    required: [true, 'Password is required'],
    minlength: [8, 'Password must be at least 8 characters long']
  },
  name: {
    type: String,
    required: [true, 'Name is required'],
    trim: true,
    maxlength: [50, 'Name cannot exceed 50 characters']
  },
  profile: {
    avatar: {
      type: String,
      default: ''
    },
    campus: {
      type: String,
      required: [true, 'Campus is required'],
      enum: ['Any campus', 'Kattankulathur (KTR)', 'Vadapalani', 'Ramapuram', 'Delhi NCR', 'Sonepat', 'Amaravati'],
      default: 'Any campus'
    },
    focus: {
      type: String,
      required: [true, 'Focus area is required'],
      enum: ['General', 'Admissions', 'Academics', 'Hostel', 'Fees', 'Placements', 'Events'],
      default: 'General'
    },
    bio: {
      type: String,
      maxlength: [200, 'Bio cannot exceed 200 characters']
    },
    preferences: {
      theme: {
        type: String,
        enum: ['light', 'dark', 'auto'],
        default: 'auto'
      },
      notifications: {
        type: Boolean,
        default: true
      },
      aiPersonality: {
        type: String,
        default: 'friendly'
      }
    }
  },
  aiTraining: {
    isEnabled: {
      type: Boolean,
      default: true
    },
    trainingData: [{
      question: {
        type: String,
        required: true
      },
      answer: {
        type: String,
        required: true
      },
      confidence: {
        type: Number,
        min: 0,
        max: 1,
        default: 0.8
      },
      timestamp: {
        type: Date,
        default: Date.now
      }
    }],
    customResponses: [{
      trigger: {
        type: String,
        required: true
      },
      response: {
        type: String,
        required: true
      },
      priority: {
        type: Number,
        min: 1,
        max: 10,
        default: 5
      }
    }],
    learningRate: {
      type: Number,
      min: 0.001,
      max: 0.1,
      default: 0.01
    },
    lastTraining: {
      type: Date,
      default: Date.now
    }
  },
  usage: {
    totalChats: {
      type: Number,
      default: 0
    },
    totalTokens: {
      type: Number,
      default: 0
    },
    lastActive: {
      type: Date,
      default: Date.now
    },
    plan: {
      type: String,
      enum: ['free', 'premium', 'enterprise'],
      default: 'free'
    }
  },
  isActive: {
    type: Boolean,
    default: true
  },
  isAdmin: {
    type: Boolean,
    default: false
  }
}, {
  timestamps: true,
  toJSON: {
    transform: (doc, ret) => {
      delete ret.password;
      return ret;
    }
  }
});

// Indexes for better query performance
userSchema.index({ email: 1 });
userSchema.index({ 'profile.campus': 1 });
userSchema.index({ 'profile.focus': 1 });
userSchema.index({ createdAt: -1 });

// Hash password before saving
userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) return next();
  
  try {
    const salt = await bcrypt.genSalt(12);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (error) {
    next(error as Error);
  }
});

// Compare password method
userSchema.methods.comparePassword = async function(candidatePassword: string): Promise<boolean> {
  try {
    return await bcrypt.compare(candidatePassword, this.password);
  } catch (error) {
    throw new Error('Password comparison failed');
  }
};

// Update last active timestamp
userSchema.methods.updateLastActive = function(): void {
  this.usage.lastActive = new Date();
  this.save().catch(console.error);
};

// Add training data
userSchema.methods.addTrainingData = function(question: string, answer: string, confidence: number): void {
  this.aiTraining.trainingData.push({
    question,
    answer,
    confidence,
    timestamp: new Date()
  });
  
  // Keep only last 1000 training examples
  if (this.aiTraining.trainingData.length > 1000) {
    this.aiTraining.trainingData = this.aiTraining.trainingData.slice(-1000);
  }
  
  this.save().catch(console.error);
};

// Add custom response
userSchema.methods.addCustomResponse = function(trigger: string, response: string, priority: number = 5): void {
  this.aiTraining.customResponses.push({
    trigger,
    response,
    priority
  });
  
  // Sort by priority (highest first)
  this.aiTraining.customResponses.sort((a, b) => b.priority - a.priority);
  
  this.save().catch(console.error);
};

export const User = mongoose.model<IUser>('User', userSchema);


