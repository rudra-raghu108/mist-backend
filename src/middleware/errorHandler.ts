import { Request, Response, NextFunction } from 'express';
import { logger } from '../utils/logger';

export interface CustomError extends Error {
  statusCode?: number;
  isOperational?: boolean;
}

export const errorHandler = (
  err: CustomError,
  req: Request,
  res: Response,
  _next: NextFunction
): void => {
  let error = { ...err };
  error.message = err.message;

  // Log error
  logger.error(`Error: ${err.message}`);
  logger.error(`Stack: ${err.stack}`);

  // Mongoose bad ObjectId
  if (err.name === 'CastError') {
    const message = 'Resource not found';
    error = new Error(message) as CustomError;
    error.statusCode = 404;
  }

  // Mongoose duplicate key
  if (err.name === 'MongoError' && (err as any).code === 11000) {
    const message = 'Duplicate field value entered';
    error = new Error(message) as CustomError;
    error.statusCode = 400;
  }

  // Mongoose validation error
  if (err.name === 'ValidationError') {
    const message = Object.values((err as any).errors).map((val: any) => val.message).join(', ');
    error = new Error(message) as CustomError;
    error.statusCode = 400;
  }

  // JWT errors
  if (err.name === 'JsonWebTokenError') {
    const message = 'Invalid token';
    error = new Error(message) as CustomError;
    error.statusCode = 401;
  }

  if (err.name === 'TokenExpiredError') {
    const message = 'Token expired';
    error = new Error(message) as CustomError;
    error.statusCode = 401;
  }

  // OpenAI API errors
  if (err.message.includes('OpenAI API')) {
    error.statusCode = 503;
  }

  // Rate limit errors
  if (err.message.includes('Too many requests')) {
    error.statusCode = 429;
  }

  // Default error
  const statusCode = error.statusCode || 500;
  const message = error.message || 'Internal Server Error';

  // Don't leak error details in production
  const isDevelopment = process.env['NODE_ENV'] === 'development';
  const errorResponse = {
    success: false,
    error: {
      message,
      ...(isDevelopment && { stack: err.stack }),
      ...(isDevelopment && { details: err })
    },
    timestamp: new Date().toISOString(),
    path: req.path,
    method: req.method
  };

  res.status(statusCode).json(errorResponse);
};
