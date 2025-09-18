import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import PromptToUML from '../pages/prompt-to-uml';

describe('PromptToUML Page', () => {
  test('renders prompt input and button', () => {
    render(<PromptToUML />);
    expect(screen.getByPlaceholderText(/describe your system/i)).toBeInTheDocument();
    expect(screen.getByText(/generate uml/i)).toBeInTheDocument();
  });

  test('disables button when prompt is empty', () => {
    render(<PromptToUML />);
    const button = screen.getByText(/generate uml/i);
    expect(button).toBeDisabled();
  });

  test('shows loading state when generating', () => {
    render(<PromptToUML />);
    const textarea = screen.getByPlaceholderText(/describe your system/i);
    fireEvent.change(textarea, { target: { value: 'A system with users and orders' } });
    const button = screen.getByText(/generate uml/i);
    fireEvent.click(button);
    expect(button).toHaveTextContent(/generating/i);
  });
});
