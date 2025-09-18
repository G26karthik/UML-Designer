/**
 * Error Handler Utilities Test Suite
 */
import { AppError, categorizeError, createUserMessage, ErrorTypes } from '../utils/errorHandler';

describe('Error Handler Utils', () => {
  describe('AppError', () => {
    test('creates AppError with required properties', () => {
      const error = new AppError('Test error', ErrorTypes.VALIDATION);
      
      expect(error.message).toBe('Test error');
      expect(error.name).toBe('AppError');
      expect(error.type).toBe(ErrorTypes.VALIDATION);
      expect(error.isRetryable).toBe(false);
      expect(error.timestamp).toBeDefined();
    });

    test('creates retryable error', () => {
      const error = new AppError('Network error', ErrorTypes.NETWORK);
      
      expect(error.isRetryable).toBe(true);
    });

    test('creates error with details and cause', () => {
      const cause = new Error('Original error');
      const error = new AppError('Test error', ErrorTypes.SERVER, { status: 500 }, cause);
      
      expect(error.details).toEqual({ status: 500 });
      expect(error.cause).toBe(cause);
    });

    test('sets timestamp as ISO string', () => {
      const error = new AppError('Test error', ErrorTypes.UNKNOWN);
      
      expect(typeof error.timestamp).toBe('string');
      expect(new Date(error.timestamp)).toBeInstanceOf(Date);
    });
  });

  describe('categorizeError', () => {
    test('categorizes network fetch errors', () => {
      const networkError = new Error('fetch failed');
      networkError.name = 'TypeError';
      
      const result = categorizeError(networkError);
      
      expect(result.type).toBe(ErrorTypes.NETWORK);
      expect(result.isRetryable).toBe(true);
      expect(result.message).toBe('Network connection failed');
    });

    test('categorizes validation errors by message content', () => {
      const validationError = new Error('Invalid GitHub URL');
      
      const result = categorizeError(validationError);
      
      expect(result.type).toBe(ErrorTypes.VALIDATION);
      expect(result.isRetryable).toBe(false);
      expect(result.message).toBe('Invalid GitHub URL');
    });

    test('categorizes timeout errors by name', () => {
      const timeoutError = new Error('timeout');
      timeoutError.name = 'TimeoutError';
      
      const result = categorizeError(timeoutError);
      
      expect(result.type).toBe(ErrorTypes.TIMEOUT);
      expect(result.isRetryable).toBe(true);
      expect(result.message).toBe('Request timed out');
    });

    test('categorizes abort errors', () => {
      const abortError = new Error('aborted');
      abortError.name = 'AbortError';
      
      const result = categorizeError(abortError);
      
      expect(result.type).toBe(ErrorTypes.TIMEOUT);
      expect(result.isRetryable).toBe(true);
      expect(result.message).toBe('Request was cancelled');
    });

    test('categorizes HTTP client errors', () => {
      const clientError = new Error('Bad request');
      clientError.status = 400;
      
      const result = categorizeError(clientError);
      
      expect(result.type).toBe(ErrorTypes.VALIDATION);
      expect(result.isRetryable).toBe(false);
      expect(result.details).toEqual({ status: 400 });
    });

    test('categorizes HTTP server errors', () => {
      const serverError = new Error('Internal server error');
      serverError.status = 500;
      
      const result = categorizeError(serverError);
      
      expect(result.type).toBe(ErrorTypes.SERVER);
      expect(result.isRetryable).toBe(true);
      expect(result.details).toEqual({ status: 500 });
    });

    test('handles unknown errors', () => {
      const unknownError = new Error('Mysterious error');
      
      const result = categorizeError(unknownError);
      
      expect(result.type).toBe(ErrorTypes.UNKNOWN);
      expect(result.isRetryable).toBe(false);
      expect(result.message).toBe('Mysterious error');
    });
  });

  describe('createUserMessage', () => {
    test('creates user-friendly network error message', () => {
      const error = new Error('fetch failed');
      error.name = 'TypeError';
      
      const message = createUserMessage(error);
      
      expect(message.title).toBe('Connection Problem');
      expect(message.message).toContain('connection');
      expect(message.action).toBe('Retry');
    });

    test('creates user-friendly validation error message', () => {
      const error = new Error('Invalid GitHub URL');
      
      const message = createUserMessage(error);
      
      expect(message.title).toBe('Invalid Input');
      expect(message.message).toBe('Invalid GitHub URL');
      expect(message.action).toBe('Fix Input');
    });

    test('creates user-friendly timeout error message', () => {
      const error = new Error('timeout');
      error.name = 'TimeoutError';
      
      const message = createUserMessage(error);
      
      expect(message.title).toBe('Request Timed Out');
      expect(message.message).toContain('taking longer');
      expect(message.action).toBe('Try Again');
    });

    test('creates user-friendly server error message', () => {
      const error = new Error('Server error');
      error.status = 500;
      
      const message = createUserMessage(error);
      
      expect(message.title).toBe('Server Error');
      expect(message.message).toContain('service is experiencing');
      expect(message.action).toBe('Retry Later');
    });

    test('creates generic message for unknown errors', () => {
      const error = new Error('Mysterious error');
      
      const message = createUserMessage(error);
      
      expect(message.title).toBe('Unexpected Error');
      expect(message.message).toBe('Mysterious error');
      expect(message.action).toBe('Try Again');
    });

    test('handles errors without message', () => {
      const error = new Error();
      
      const message = createUserMessage(error);
      
      expect(message.title).toBe('Unexpected Error');
      expect(message.message).toBe('An unexpected error occurred');
      expect(message.action).toBe('Try Again');
    });

    test('handles AppError instances directly', () => {
      const appError = new AppError('Custom validation error', ErrorTypes.VALIDATION);
      
      const message = createUserMessage(appError);
      
      expect(message.title).toBe('Invalid Input');
      expect(message.message).toBe('Custom validation error');
      expect(message.action).toBe('Fix Input');
    });
  });
});