import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { User, IUser } from '../models/User';
import { logger } from '../utils/logger';

// Extend Express Request interface to include user
declare global {
  namespace Express {
    interface Request {
      user?: IUser;
    }
  }
}

export const protect = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  let token: string | undefined;

  // Check for token in headers
  if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
    token = req.headers.authorization.split(' ')[1];
  }

  // Check for token in cookies
  if (!token && req.cookies?.token) {
    token = req.cookies.token;
  }

  if (!token) {
    res.status(401).json({
      success: false,
      error: {
        message: 'Not authorized to access this route',
        code: 'NO_TOKEN'
      }
    });
    return;
  }

  try {
    // Verify token
    const decoded = jwt.verify(token, process.env['JWT_SECRET']!) as { id: string };
    
    // Get user from token
    const user = await User.findById(decoded.id).select('-password');
    
    if (!user) {
      res.status(401).json({
        success: false,
        error: {
          message: 'User not found',
          code: 'USER_NOT_FOUND'
        }
      });
      return;
    }

    if (!user.isActive) {
      res.status(401).json({
        success: false,
        error: {
          message: 'User account is deactivated',
          code: 'USER_DEACTIVATED'
        }
      });
      return;
    }

    // Update last active timestamp
    user.updateLastActive();
    
    // Add user to request
    req.user = user;
    next();
  } catch (error) {
    logger.error('Token verification failed:', error);
    res.status(401).json({
      success: false,
      error: {
        message: 'Not authorized to access this route',
        code: 'INVALID_TOKEN'
      }
    });
  }
};

export const authorize = (...roles: string[]) => {
  return (req: Request, res: Response, next: NextFunction): void => {
    if (!req.user) {
      res.status(401).json({
        success: false,
        error: {
          message: 'User not authenticated',
          code: 'NOT_AUTHENTICATED'
        }
      });
      return;
    }

    if (!roles.includes(req.user.profile.focus) && !req.user.isAdmin) {
      res.status(403).json({
        success: false,
        error: {
          message: 'User role is not authorized to access this route',
          code: 'INSUFFICIENT_PERMISSIONS'
        }
      });
      return;
    }

    next();
  };
};

export const requireAdmin = (req: Request, res: Response, next: NextFunction): void => {
  if (!req.user?.isAdmin) {
    res.status(403).json({
      success: false,
      error: {
        message: 'Admin access required',
        code: 'ADMIN_ACCESS_REQUIRED'
      }
    });
    return;
  }

  next();
};

export const optionalAuth = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  let token: string | undefined;

  // Check for token in headers
  if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
    token = req.headers.authorization.split(' ')[1];
  }

  // Check for token in cookies
  if (!token && req.cookies?.token) {
    token = req.cookies.token;
  }

  if (token) {
    try {
      const decoded = jwt.verify(token, process.env['JWT_SECRET']!) as { id: string };
      const user = await User.findById(decoded.id).select('-password');
      
      if (user && user.isActive) {
        user.updateLastActive();
        req.user = user;
      }
    } catch (error) {
      // Token is invalid, but we continue without authentication
      logger.debug('Optional auth failed, continuing without user');
    }
  }

  next();
};
