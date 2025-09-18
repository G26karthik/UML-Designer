import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import Home from '../pages/index';

test('renders input and button', () => {
  render(<Home />);
  expect(screen.getByPlaceholderText(/github repo url/i)).toBeInTheDocument();
  expect(screen.getByText('Analyze')).toBeInTheDocument();
});

test('renders diagram type selector', () => {
  render(<Home />);
  expect(screen.getByText('Diagram:')).toBeInTheDocument();
  expect(screen.getByText('Class')).toBeInTheDocument();
  expect(screen.getByText('Use Case')).toBeInTheDocument();
  expect(screen.getByText('Activity')).toBeInTheDocument();
  expect(screen.getByText('Sequence')).toBeInTheDocument();
  expect(screen.getByText('State')).toBeInTheDocument();
});
