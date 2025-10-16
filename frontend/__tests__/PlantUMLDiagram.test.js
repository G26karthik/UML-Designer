/**
 * PlantUMLDiagram Component Test Suite
 * Tests PlantUML rendering, error handling, and export functionality
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PlantUMLDiagram from '../components/PlantUMLDiagram';

// Mock plantuml-encoder
jest.mock('plantuml-encoder', () => ({
  encode: jest.fn((text) => `encoded_${btoa(text)}`)
}));

// Mock fetch
global.fetch = jest.fn();

describe('PlantUMLDiagram Component', () => {
  beforeEach(() => {
    fetch.mockClear();
    jest.clearAllMocks();
  });

  // ============================================================================
  // Test Basic Rendering
  // ============================================================================

  test('renders loading state initially', () => {
    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    expect(screen.getByText(/Loading PlantUML diagram/i)).toBeInTheDocument();
  });

  test('renders diagram image after successful load', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      const img = screen.getByRole('img');
      expect(img).toBeInTheDocument();
    });
  });

  test('displays error message on fetch failure', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to render PlantUML diagram/i)).toBeInTheDocument();
    });
  });

  test('displays error when server returns error response', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error'
    });

    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to render PlantUML diagram/i)).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Test UML Input Variations
  // ============================================================================

  test('handles simple class diagram UML', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    const uml = `@startuml
class User {
  - id: int
  + email: string
}
@enduml`;
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      expect(screen.getByRole('img')).toBeInTheDocument();
    });
  });

  test('handles complex class diagram with relationships', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    const uml = `@startuml
interface IRepository <<interface>>
abstract class BaseEntity <<abstract>>
class User {
  - id: int
}
User --|> BaseEntity
UserService ..|> IRepository
@enduml`;
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      expect(screen.getByRole('img')).toBeInTheDocument();
    });
  });

  test('handles empty UML', async () => {
    const uml = '@startuml\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    // Should not crash, may show loading or empty state
    expect(screen.getByText(/Loading PlantUML diagram/i)).toBeInTheDocument();
  });

  test('handles invalid UML syntax', async () => {
    const uml = 'not valid plantuml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    // Should handle gracefully
    expect(screen.getByText(/Loading PlantUML diagram/i)).toBeInTheDocument();
  });

  // ============================================================================
  // Test Export Functionality
  // ============================================================================

  test('renders copy button', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Copy PlantUML/i)).toBeInTheDocument();
    });
  });

  test('copy button copies UML to clipboard', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn().mockResolvedValue()
      }
    });

    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      const copyButton = screen.getByText(/Copy PlantUML/i);
      fireEvent.click(copyButton);
    });

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(uml);
    });
  });

  test('renders download button', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Download SVG/i)).toBeInTheDocument();
    });
  });

  test('download button triggers download', async () => {
    const mockBlob = new Blob(['<svg></svg>'], { type: 'image/svg+xml' });
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(mockBlob)
    });
    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    // Mock URL.createObjectURL
    global.URL.createObjectURL = jest.fn(() => 'blob:mock-url');
    global.URL.revokeObjectURL = jest.fn();

    // Mock createElement only for anchor tags so React's internal creates are
    // not affected. Save native implementation so we can forward other tags.
    const nativeCreateElement = document.createElement.bind(document);
    const mockLink = {
      click: jest.fn(),
      setAttribute: jest.fn(),
      style: {}
    };

    const createElementSpy = jest.spyOn(document, 'createElement').mockImplementation((tagName, options) => {
      if (tagName === 'a') return mockLink;
      return nativeCreateElement(tagName, options);
    });

    // Let appendChild/removeChild behave normally
    const appendSpy = jest.spyOn(document.body, 'appendChild').mockImplementation((el) => nativeCreateElement('div').appendChild?.call?.(el) || undefined);
    const removeSpy = jest.spyOn(document.body, 'removeChild').mockImplementation(() => {});

    try {
      await waitFor(() => {
        const downloadButton = screen.getByText(/Download SVG/i);
        fireEvent.click(downloadButton);
      });

      await waitFor(() => {
        expect(mockLink.click).toHaveBeenCalled();
      });
    } finally {
      createElementSpy.mockRestore();
      appendSpy.mockRestore();
      removeSpy.mockRestore();
    }
  });

  // ============================================================================
  // Test Error Handling
  // ============================================================================

  test('shows retry button on error', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Retry/i)).toBeInTheDocument();
    });
  });

  test('retry button triggers new fetch attempt', async () => {
    // First call fails
    fetch.mockRejectedValueOnce(new Error('Network error'));
    // Second call succeeds
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      const retryButton = screen.getByText(/Retry/i);
      fireEvent.click(retryButton);
    });

    await waitFor(() => {
      expect(screen.getByRole('img')).toBeInTheDocument();
    });

    expect(fetch).toHaveBeenCalledTimes(2);
  });

  test('handles timeout errors gracefully', async () => {
    fetch.mockImplementationOnce(() => 
      new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            ok: false,
            status: 504,
            statusText: 'Gateway Timeout'
          });
        }, 100);
      })
    );

    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to render PlantUML diagram/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  // ============================================================================
  // Test Props Variations
  // ============================================================================

  test('accepts custom server URL prop', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    const uml = '@startuml\nclass User\n@enduml';
    const customServer = 'http://custom-plantuml-server.com';
    
    render(<PlantUMLDiagram uml={uml} server={customServer} />);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
      const fetchUrl = fetch.mock.calls[0][0];
      expect(fetchUrl).toContain(customServer);
    });
  });

  test('accepts custom format prop', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['data'], { type: 'image/png' }))
    });

    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} format="png" />);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
      const fetchUrl = fetch.mock.calls[0][0];
      expect(fetchUrl).toContain('png');
    });
  });

  test('updates when UML prop changes', async () => {
    fetch.mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    const uml1 = '@startuml\nclass User\n@enduml';
    const uml2 = '@startuml\nclass Order\n@enduml';
    
    const { rerender } = render(<PlantUMLDiagram uml={uml1} />);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(1);
    });

    rerender(<PlantUMLDiagram uml={uml2} />);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(2);
    });
  });

  test('does not re-fetch if UML unchanged', async () => {
    fetch.mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    const uml = '@startuml\nclass User\n@enduml';
    
    const { rerender } = render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(1);
    });

    rerender(<PlantUMLDiagram uml={uml} />);
    
    // Should not fetch again
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  // ============================================================================
  // Test Accessibility
  // ============================================================================

  test('diagram image has alt text', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      const img = screen.getByRole('img');
      expect(img).toHaveAttribute('alt');
    });
  });

  test('error message is accessible', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      const errorMessage = screen.getByText(/Failed to render PlantUML diagram/i);
      expect(errorMessage).toBeInTheDocument();
    });
  });

  test('buttons are keyboard accessible', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      const copyButton = screen.getByText(/Copy PlantUML/i);
      expect(copyButton.tagName).toBe('BUTTON');
    });
  });

  // ============================================================================
  // Test PlantUML Encoding
  // ============================================================================

  test('encodes UML before sending to server', async () => {
    const plantumlEncoder = require('plantuml-encoder');
    
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    const uml = '@startuml\nclass User\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      expect(plantumlEncoder.encode).toHaveBeenCalledWith(uml);
    });
  });

  test('handles special characters in UML', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    const uml = '@startuml\nclass User_Model_V2 {\n  - field: string\n}\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      expect(screen.getByRole('img')).toBeInTheDocument();
    });
  });

  test('handles unicode characters in UML', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['<svg></svg>'], { type: 'image/svg+xml' }))
    });

    const uml = '@startuml\nclass Usuario {\n  - contraseña: string\n}\n@enduml';
    
    render(<PlantUMLDiagram uml={uml} />);
    
    await waitFor(() => {
      expect(screen.getByRole('img')).toBeInTheDocument();
    });
  });
});
