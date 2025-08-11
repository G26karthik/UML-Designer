import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import Home from '../pages/index';

test('renders input and button', () => {
  render(<Home />);
  expect(screen.getByPlaceholderText(/github repo url/i)).toBeInTheDocument();
  expect(screen.getByText('Analyze')).toBeInTheDocument();
});
