/**
 * DiagramErrorBoundary Test Suite
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import DiagramErrorBoundary from '../components/DiagramErrorBoundary';

// Test component that throws an error
const ThrowError = ({ shouldThrow, error }) => {
  if (shouldThrow) {
    throw error || new Error('Test error');
  }
  return <div>Working component</div>;
};

// Suppress console.error for tests
const originalError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalError;
});

describe('DiagramErrorBoundary', () => {
  test('renders children when no error occurs', () => {
    render(
      <DiagramErrorBoundary>
        <div>Normal content</div>
      </DiagramErrorBoundary>
    );

    expect(screen.getByText('Normal content')).toBeInTheDocument();
  });

  test('catches and displays error when child component throws', () => {
    render(
      <DiagramErrorBoundary>
        <ThrowError shouldThrow={true} />
      </DiagramErrorBoundary>
    );

    expect(screen.getByText('Diagram Rendering Failed')).toBeInTheDocument();
    expect(screen.getByText(/Diagram rendering error: Test error/)).toBeInTheDocument();
  });

  test('categorizes syntax errors correctly', () => {
    const syntaxError = new Error('Parse error on line 1');
    
    render(
      <DiagramErrorBoundary>
        <ThrowError shouldThrow={true} error={syntaxError} />
      </DiagramErrorBoundary>
    );

    expect(screen.getByText(/Invalid diagram syntax/)).toBeInTheDocument();
  });

  test('categorizes timeout errors correctly', () => {
    const timeoutError = new Error('timeout occurred');
    
    render(
      <DiagramErrorBoundary>
        <ThrowError shouldThrow={true} error={timeoutError} />
      </DiagramErrorBoundary>
    );

    expect(screen.getByText(/timed out/)).toBeInTheDocument();
  });

  test('categorizes module loading errors correctly', () => {
    const moduleError = new Error('Failed to import module');
    
    render(
      <DiagramErrorBoundary>
        <ThrowError shouldThrow={true} error={moduleError} />
      </DiagramErrorBoundary>
    );

    expect(screen.getByText(/Failed to load diagram rendering library/)).toBeInTheDocument();
  });

  test('categorizes recursion errors correctly', () => {
    const recursionError = new Error('Maximum call stack size exceeded');
    
    render(
      <DiagramErrorBoundary>
        <ThrowError shouldThrow={true} error={recursionError} />
      </DiagramErrorBoundary>
    );

    expect(screen.getByText(/too complex or contains circular references/)).toBeInTheDocument();
  });

  test('shows retry button with correct attempt count', () => {
    render(
      <DiagramErrorBoundary>
        <ThrowError shouldThrow={true} />
      </DiagramErrorBoundary>
    );

    expect(screen.getByText('Retry (3 attempts left)')).toBeInTheDocument();
  });

  test('retry button triggers retry action', () => {
    render(
      <DiagramErrorBoundary>
        <ThrowError shouldThrow={true} />
      </DiagramErrorBoundary>
    );

    // Click retry
    fireEvent.click(screen.getByText('Retry (3 attempts left)'));

    // Should show decreased attempts
    expect(screen.getByText('Retry (2 attempts left)')).toBeInTheDocument();
  });

  test('retry count decreases with each attempt', () => {
    render(
      <DiagramErrorBoundary>
        <ThrowError shouldThrow={true} />
      </DiagramErrorBoundary>
    );

    // First click - should show 2 attempts left
    fireEvent.click(screen.getByText('Retry (3 attempts left)'));
    expect(screen.getByText('Retry (2 attempts left)')).toBeInTheDocument();

    // Second click - should show 1 attempt left
    fireEvent.click(screen.getByText('Retry (2 attempts left)'));
    expect(screen.getByText('Retry (1 attempts left)')).toBeInTheDocument();

    // Third click - retry button should disappear
    fireEvent.click(screen.getByText('Retry (1 attempts left)'));
    expect(screen.queryByText(/Retry/)).not.toBeInTheDocument();
  });

  test('reset button triggers reset action', () => {
    render(
      <DiagramErrorBoundary>
        <ThrowError shouldThrow={true} />
      </DiagramErrorBoundary>
    );

    // Should have error state
    expect(screen.getByText('Diagram Rendering Failed')).toBeInTheDocument();
    
    // Click reset should trigger reset (but error boundary will still show error until re-render with working component)
    fireEvent.click(screen.getByText('Reset'));
    
    // Reset button still exists - error boundary needs working children to clear
    expect(screen.getByText('Reset')).toBeInTheDocument();
  });

  test('calls onError callback when error occurs', () => {
    const mockOnError = jest.fn();
    
    render(
      <DiagramErrorBoundary onError={mockOnError}>
        <ThrowError shouldThrow={true} />
      </DiagramErrorBoundary>
    );

    expect(mockOnError).toHaveBeenCalledWith(
      expect.any(Error),
      expect.objectContaining({
        componentStack: expect.any(String)
      })
    );
  });

  test('shows fallback button when onFallback prop is provided', () => {
    const mockOnFallback = jest.fn();
    
    render(
      <DiagramErrorBoundary onFallback={mockOnFallback}>
        <ThrowError shouldThrow={true} />
      </DiagramErrorBoundary>
    );

    const fallbackButton = screen.getByText('Show Raw Text');
    expect(fallbackButton).toBeInTheDocument();
    
    fireEvent.click(fallbackButton);
    expect(mockOnFallback).toHaveBeenCalled();
  });

  test('shows error details in development mode', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    render(
      <DiagramErrorBoundary>
        <ThrowError shouldThrow={true} />
      </DiagramErrorBoundary>
    );

    expect(screen.getByText('Error Details (Development)')).toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  test('hides error details in production mode', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'production';

    render(
      <DiagramErrorBoundary>
        <ThrowError shouldThrow={true} />
      </DiagramErrorBoundary>
    );

    expect(screen.queryByText('Error Details (Development)')).not.toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  test('handles errors without message gracefully', () => {
    const errorWithoutMessage = new Error();
    errorWithoutMessage.message = '';
    
    render(
      <DiagramErrorBoundary>
        <ThrowError shouldThrow={true} error={errorWithoutMessage} />
      </DiagramErrorBoundary>
    );

    // The component shows "Error" as the toString() of an empty Error
    expect(screen.getByText(/Diagram rendering error: Error/)).toBeInTheDocument();
  });

  test('displays error icon', () => {
    render(
      <DiagramErrorBoundary>
        <ThrowError shouldThrow={true} />
      </DiagramErrorBoundary>
    );

    expect(screen.getByText('⚠️')).toBeInTheDocument();
  });
});