import { Request, Response } from 'express';
import { logger } from '../utils/logger';

export const notFound = (req: Request, res: Response): void => {
  logger.warn(`Route not found: ${req.method} ${req.originalUrl}`);
  
  res.status(404).json({
    success: false,
    error: {
      message: `Route ${req.method} ${req.originalUrl} not found`,
      code: 'ROUTE_NOT_FOUND'
    },
    timestamp: new Date().toISOString(),
    suggestions: [
      'Check the URL for typos',
      'Verify the HTTP method (GET, POST, PUT, DELETE)',
      'Ensure the API endpoint exists',
      'Check the API documentation'
    ]
  });
};
