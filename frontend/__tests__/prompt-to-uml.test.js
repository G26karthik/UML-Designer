import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PromptToUML from '../pages/prompt-to-uml';

describe('PromptToUML Page', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ diagram: '@startuml\n@enduml' })
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      delete global.fetch;
    }
  });

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

  test('shows loading state when generating', async () => {
    render(<PromptToUML />);
    const textarea = screen.getByPlaceholderText(/describe your system/i);
    fireEvent.change(textarea, { target: { value: 'A system with users and orders' } });
    const button = screen.getByText(/generate uml/i);
    fireEvent.click(button);

    expect(button).toHaveTextContent(/generating/i);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(global.fetch.mock.calls[0][0]).toContain('/api/v1/uml-from-prompt');
    });

    await waitFor(() => expect(button).toHaveTextContent(/generate uml/i));
  });
});
