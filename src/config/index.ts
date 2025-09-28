import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

interface Config {
  // Server
  nodeEnv: string;
  port: number;
  apiVersion: string;
  
  // Database
  database: {
    url: string;
    urlTest: string;
  };
  
  // Redis
  redis: {
    url: string;
    password?: string;
  };
  
  // JWT
  jwt: {
    secret: string;
    expiresIn: string;
    refreshSecret: string;
    refreshExpiresIn: string;
  };
  
  // OpenAI
  openai: {
    apiKey: string;
    model: string;
    maxTokens: number;
    temperature: number;
  };
  
  // Google OAuth
  google: {
    clientId: string;
    clientSecret: string;
    callbackUrl: string;
  };
  
  // Email
  email: {
    host: string;
    port: number;
    user: string;
    pass: string;
    from: string;
  };
  
  // SMS (Twilio)
  twilio: {
    accountSid: string;
    authToken: string;
    phoneNumber: string;
  };
  
  // AWS
  aws: {
    accessKeyId: string;
    secretAccessKey: string;
    region: string;
    s3Bucket: string;
  };
  
  // Stripe
  stripe: {
    secretKey: string;
    webhookSecret: string;
    publishableKey: string;
  };
  
  // Rate Limiting
  rateLimit: {
    windowMs: number;
    maxRequests: number;
  };
  
  // File Upload
  fileUpload: {
    maxSize: number;
    allowedTypes: string[];
  };
  
  // Logging
  logging: {
    level: string;
    filePath: string;
  };
  
  // CORS
  cors: {
    origin: string | string[];
    credentials: boolean;
  };
  
  // Session
  session: {
    secret: string;
    cookieSecure: boolean;
    cookieHttpOnly: boolean;
    cookieMaxAge: number;
  };
  
  // Feature Flags
  features: {
    emailVerification: boolean;
    smsVerification: boolean;
    googleOAuth: boolean;
    paymentIntegration: boolean;
    realTimeChat: boolean;
    analytics: boolean;
  };
  
  // Analytics
  analytics: {
    enabled: boolean;
    provider: string;
    mixpanelToken: string;
  };
  
  // Monitoring
  monitoring: {
    sentryDsn: string;
    newRelicKey: string;
  };
  
  // Cache
  cache: {
    ttl: number;
    checkPeriod: number;
  };
  
  // Security
  security: {
    bcryptRounds: number;
    passwordMinLength: number;
    passwordRequireSpecialChars: boolean;
    passwordRequireNumbers: boolean;
    passwordRequireUppercase: boolean;
  };
}

const config: Config = {
  // Server
  nodeEnv: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT || '5000', 10),
  apiVersion: process.env.API_VERSION || 'v1',
  
  // Database
  database: {
    url: process.env.DATABASE_URL || 'postgresql://username:password@localhost:5432/srm_guide_bot',
    urlTest: process.env.DATABASE_URL_TEST || 'postgresql://username:password@localhost:5432/srm_guide_bot_test',
  },
  
  // Redis
  redis: {
    url: process.env.REDIS_URL || 'redis://localhost:6379',
    password: process.env.REDIS_PASSWORD,
  },
  
  // JWT
  jwt: {
    secret: process.env.JWT_SECRET || 'your-super-secret-jwt-key-change-this-in-production',
    expiresIn: process.env.JWT_EXPIRES_IN || '7d',
    refreshSecret: process.env.JWT_REFRESH_SECRET || 'your-refresh-secret-key',
    refreshExpiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '30d',
  },
  
  // OpenAI
  openai: {
    apiKey: process.env.OPENAI_API_KEY || '',
    model: process.env.OPENAI_MODEL || 'gpt-4',
    maxTokens: parseInt(process.env.OPENAI_MAX_TOKENS || '2000', 10),
    temperature: parseFloat(process.env.OPENAI_TEMPERATURE || '0.7'),
  },
  
  // Google OAuth
  google: {
    clientId: process.env.GOOGLE_CLIENT_ID || '',
    clientSecret: process.env.GOOGLE_CLIENT_SECRET || '',
    callbackUrl: process.env.GOOGLE_CALLBACK_URL || 'http://localhost:5000/api/v1/auth/google/callback',
  },
  
  // Email
  email: {
    host: process.env.EMAIL_HOST || 'smtp.gmail.com',
    port: parseInt(process.env.EMAIL_PORT || '587', 10),
    user: process.env.EMAIL_USER || '',
    pass: process.env.EMAIL_PASS || '',
    from: process.env.EMAIL_FROM || 'SRM Guide Bot <noreply@srmguidebot.com>',
  },
  
  // SMS (Twilio)
  twilio: {
    accountSid: process.env.TWILIO_ACCOUNT_SID || '',
    authToken: process.env.TWILIO_AUTH_TOKEN || '',
    phoneNumber: process.env.TWILIO_PHONE_NUMBER || '',
  },
  
  // AWS
  aws: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || '',
    region: process.env.AWS_REGION || 'us-east-1',
    s3Bucket: process.env.AWS_S3_BUCKET || 'srm-guide-bot-uploads',
  },
  
  // Stripe
  stripe: {
    secretKey: process.env.STRIPE_SECRET_KEY || '',
    webhookSecret: process.env.STRIPE_WEBHOOK_SECRET || '',
    publishableKey: process.env.STRIPE_PUBLISHABLE_KEY || '',
  },
  
  // Rate Limiting
  rateLimit: {
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000', 10),
    maxRequests: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100', 10),
  },
  
  // File Upload
  fileUpload: {
    maxSize: parseInt(process.env.MAX_FILE_SIZE || '5242880', 10),
    allowedTypes: (process.env.ALLOWED_FILE_TYPES || 'image/jpeg,image/png,image/gif,application/pdf').split(','),
  },
  
  // Logging
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    filePath: process.env.LOG_FILE_PATH || 'logs/app.log',
  },
  
  // CORS
  cors: {
    origin: process.env.CORS_ORIGIN ? process.env.CORS_ORIGIN.split(',') : 'http://localhost:3000',
    credentials: process.env.CORS_CREDENTIALS === 'true',
  },
  
  // Session
  session: {
    secret: process.env.SESSION_SECRET || 'your-session-secret-key',
    cookieSecure: process.env.SESSION_COOKIE_SECURE === 'true',
    cookieHttpOnly: process.env.SESSION_COOKIE_HTTPONLY !== 'false',
    cookieMaxAge: parseInt(process.env.SESSION_COOKIE_MAX_AGE || '86400000', 10),
  },
  
  // Feature Flags
  features: {
    emailVerification: process.env.ENABLE_EMAIL_VERIFICATION === 'true',
    smsVerification: process.env.ENABLE_SMS_VERIFICATION === 'true',
    googleOAuth: process.env.ENABLE_GOOGLE_OAUTH === 'true',
    paymentIntegration: process.env.ENABLE_PAYMENT_INTEGRATION === 'true',
    realTimeChat: process.env.ENABLE_REAL_TIME_CHAT === 'true',
    analytics: process.env.ENABLE_ANALYTICS === 'true',
  },
  
  // Analytics
  analytics: {
    enabled: process.env.ANALYTICS_ENABLED === 'true',
    provider: process.env.ANALYTICS_PROVIDER || 'mixpanel',
    mixpanelToken: process.env.MIXPANEL_TOKEN || '',
  },
  
  // Monitoring
  monitoring: {
    sentryDsn: process.env.SENTRY_DSN || '',
    newRelicKey: process.env.NEW_RELIC_LICENSE_KEY || '',
  },
  
  // Cache
  cache: {
    ttl: parseInt(process.env.CACHE_TTL || '3600', 10),
    checkPeriod: parseInt(process.env.CACHE_CHECK_PERIOD || '600', 10),
  },
  
  // Security
  security: {
    bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS || '12', 10),
    passwordMinLength: parseInt(process.env.PASSWORD_MIN_LENGTH || '8', 10),
    passwordRequireSpecialChars: process.env.PASSWORD_REQUIRE_SPECIAL_CHARS === 'true',
    passwordRequireNumbers: process.env.PASSWORD_REQUIRE_NUMBERS === 'true',
    passwordRequireUppercase: process.env.PASSWORD_REQUIRE_UPPERCASE === 'true',
  },
};

// Validate required configuration
const validateConfig = () => {
  const requiredFields = [
    'jwt.secret',
    'openai.apiKey',
    'database.url',
  ];

  const missingFields = requiredFields.filter(field => {
    const keys = field.split('.');
    let value: any = config;
    for (const key of keys) {
      value = value[key];
    }
    return !value;
  });

  if (missingFields.length > 0) {
    throw new Error(`Missing required configuration: ${missingFields.join(', ')}`);
  }
};

// Validate configuration in production
if (config.nodeEnv === 'production') {
  validateConfig();
}

export { config };
