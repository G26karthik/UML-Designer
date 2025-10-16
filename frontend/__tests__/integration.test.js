/**
 * Frontend Integration Tests
 * Tests full component flows and user interactions
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import HomePage from '../components/HomePage';

// Mock the dynamic imports
jest.mock('next/dynamic', () => ({
  __esModule: true,
  default: (componentImport) => {
    // Return a mock component that renders immediately
    const MockComponent = () => {
      const React = require('react');
      return React.createElement('div', { 'data-testid': 'mock-diagram' }, 'Mock Diagram');
    };
    return MockComponent;
  }
}));

// Mock the diagram components directly as well


jest.mock('../components/PlantUMLDiagram', () => {
  const React = require('react');
  return React.forwardRef(() => React.createElement('div', { 'data-testid': 'plantuml-diagram' }, 'PlantUML Diagram Rendered'));
});

jest.mock('../components/DiagramErrorBoundary', () => {
  const React = require('react');
  return ({ children }) => React.createElement('div', { 'data-testid': 'diagram-error-boundary' }, children);
});

// Mock the API request utility
jest.mock('../utils/config', () => ({
  validateGitHubUrl: jest.fn(),
  apiRequest: jest.fn()
}));

jest.mock('../utils/diagramBuilder', () => ({
  buildDiagram: jest.fn(),
  validateSchema: jest.fn(),
  getAvailableLanguages: jest.fn(),
  getDiagramStats: jest.fn()
}));


const mockValidateGitHubUrl = require('../utils/config').validateGitHubUrl;
const mockApiRequest = require('../utils/config').apiRequest;
const mockBuildDiagram = require('../utils/diagramBuilder').buildDiagram;
const mockValidateSchema = require('../utils/diagramBuilder').validateSchema;
const mockGetAvailableLanguages = require('../utils/diagramBuilder').getAvailableLanguages;

describe('Frontend Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default mocks
    mockValidateGitHubUrl.mockReturnValue({ isValid: true, url: 'https://github.com/test/repo' });
    mockApiRequest.mockResolvedValue({
      schema: {
        python: [{ class: 'TestClass', fields: ['field1'], methods: ['method1'] }],
        meta: { commit: 'abc123', files_scanned: 10 }
      }
    });
    mockValidateSchema.mockReturnValue({ isValid: true });
    mockGetAvailableLanguages.mockReturnValue(['python']);
    mockBuildDiagram.mockReturnValue('classDiagram\nTestClass {\n  field1\n  method1()\n}');
    mockUseErrorHandler.mockReturnValue({
      clearError: jest.fn(),
      handleError: jest.fn((error, operation) => {
        // Simulate setting the error state
        // The useErrorHandler hook receives setError as first parameter
        // We need to call it to update the component state
      })
    });



    // Mock clipboard
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: jest.fn().mockResolvedValue(),
      },
      writable: true,
    });
  });

  describe('Repository Analysis Flow', () => {
    test('should analyze GitHub repository and display diagram', async () => {
      render(<HomePage />);

      // Find and fill the GitHub URL input
      const urlInput = screen.getByPlaceholderText(/paste github repo url/i);
      fireEvent.change(urlInput, {
        target: { value: 'https://github.com/test/repo' }
      });

      // Click the analyze button
      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      // Wait for the diagram to appear
      await waitFor(() => {
        expect(screen.getByTestId('mock-diagram')).toBeInTheDocument();
      });

      // Verify API was called correctly
      expect(mockApiRequest).toHaveBeenCalledWith('/analyze', {
        method: 'POST',
        body: JSON.stringify({ githubUrl: 'https://github.com/test/repo' })
      });

      // Verify diagram content
      expect(screen.getByText('Mock Diagram')).toBeInTheDocument();
    });

    test('should handle analysis errors gracefully', async () => {
      // Mock API error
      mockApiRequest.mockRejectedValue(new Error('Network error'));

      render(<HomePage />);

      const urlInput = screen.getByPlaceholderText(/paste github repo url/i);
      fireEvent.change(urlInput, {
        target: { value: 'https://github.com/test/repo' }
      });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      // Wait for error handler to be called
      await waitFor(() => {
        expect(mockUseErrorHandler().handleError).toHaveBeenCalledWith(
          expect.any(Error),
          'analyze',
          expect.any(Function)
        );
      });
    });

    test('should validate GitHub URL before analysis', async () => {
      mockValidateGitHubUrl.mockReturnValue({
        isValid: false,
        error: 'Invalid GitHub URL'
      });

      render(<HomePage />);

      const urlInput = screen.getByPlaceholderText(/paste github repo url/i);
      fireEvent.change(urlInput, {
        target: { value: 'invalid-url' }
      });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      // Should show validation error
      expect(screen.getByText('Invalid GitHub URL')).toBeInTheDocument();
      expect(mockApiRequest).not.toHaveBeenCalled();
    });
  });

  describe('Prompt to UML Flow', () => {
    test('should generate diagram from natural language prompt', async () => {
      // Mock prompt API response
      mockApiRequest.mockResolvedValue({
        diagram: 'classDiagram\nUser {\n  name: string\n  login()\n}'
      });

      render(<HomePage />);

      // Find and fill the prompt input
      const promptInput = screen.getByPlaceholderText(/quick prompt/i);
      fireEvent.change(promptInput, {
        target: { value: 'Create a user class with name field and login method' }
      });

      // Click the generate button
      const generateButton = screen.getByRole('button', { name: /generate/i });
      fireEvent.click(generateButton);

      // Wait for the diagram to appear
      await waitFor(() => {
        expect(screen.getByTestId('mock-diagram')).toBeInTheDocument();
      });

      // Verify API was called correctly
      expect(mockApiRequest).toHaveBeenCalledWith('/uml-from-prompt', {
        method: 'POST',
        body: JSON.stringify({
          prompt: 'Create a user class with name field and login method',
          diagramType: 'class',
          format: 'plantuml'
        })
      });
    });

    test('should handle prompt generation errors', async () => {
      mockApiRequest.mockRejectedValue(new Error('AI service unavailable'));

      render(<HomePage />);

      const promptInput = screen.getByPlaceholderText(/quick prompt/i);
      fireEvent.change(promptInput, {
        target: { value: 'Create a simple class diagram' }
      });

      const generateButton = screen.getByRole('button', { name: /generate/i });
      fireEvent.click(generateButton);

      await waitFor(() => {
        expect(mockUseErrorHandler().handleError).toHaveBeenCalledWith(
          expect.any(Error),
          'uml-from-prompt'
        );
      });
    });
  });

  describe('Diagram Format Switching', () => {

    // Format switching test removed: PlantUML is now the only supported format.
  });

  describe('Diagram Type Selection', () => {
    test('should change diagram type and regenerate', async () => {
      render(<HomePage />);

      // Analyze repository
      const urlInput = screen.getByPlaceholderText(/paste github repo url/i);
      fireEvent.change(urlInput, {
        target: { value: 'https://github.com/test/repo' }
      });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByTestId('mock-diagram')).toBeInTheDocument();
      });

      // Change diagram type to sequence
      const diagramSelect = screen.getByDisplayValue('Class'); // The diagram type select starts with 'Class'
      fireEvent.change(diagramSelect, { target: { value: 'sequence' } });

      // Should rebuild diagram with new type
      expect(mockBuildDiagram).toHaveBeenCalledWith(
        expect.any(Object),
        'sequence',
        { python: true },
        expect.any(Object)
      );
    });
  });

  describe('Error Recovery', () => {
    test('should allow retry after analysis failure', async () => {
      // First call fails, second succeeds
      mockApiRequest
        .mockRejectedValueOnce(new Error('Network timeout'))
        .mockResolvedValueOnce({
          schema: {
            python: [{ class: 'RetryClass', fields: ['field'] }],
            meta: { commit: 'def456', files_scanned: 5 }
          }
        });

      render(<HomePage />);

      const urlInput = screen.getByPlaceholderText(/paste github repo url/i);
      fireEvent.change(urlInput, {
        target: { value: 'https://github.com/test/repo' }
      });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });

      // First attempt fails
      fireEvent.click(analyzeButton);
      await waitFor(() => {
        expect(mockUseErrorHandler().handleError).toHaveBeenCalledWith(
          expect.any(Error),
          'analyze',
          expect.any(Function)
        );
      });

      // Second attempt succeeds
      fireEvent.click(analyzeButton);
      await waitFor(() => {
        expect(screen.getByTestId('mock-diagram')).toBeInTheDocument();
      });
    });
  });
});