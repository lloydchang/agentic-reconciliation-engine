import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SkillsManagement from './SkillsManagement';

// Mock fetch
const mockSkills = {
  skills: [
    {
      name: 'test-skill',
      description: 'A test skill',
      scope: 'repo',
      userInvocable: true,
      argumentHint: 'arg1 arg2'
    }
  ]
};

beforeEach(() => {
  global.fetch = jest.fn().mockImplementation((url) => {
    if (url.includes('/api/skills')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockSkills),
      });
    }
    if (url.includes('/workflow/start-skill')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ workflowId: 'test-workflow-id' }),
      });
    }
    return Promise.reject(new Error('Unknown URL'));
  });
});

afterEach(() => {
  jest.clearAllMocks();
});

describe('SkillsManagement', () => {
  test('renders AI Agent Skills title', async () => {
    render(<SkillsManagement />);
    expect(screen.getByText(/AI Agent Skills/i)).toBeInTheDocument();
  });

  test('fetches and displays skills', async () => {
    render(<SkillsManagement />);
    
    // Wait for the skill to be displayed
    const skillName = await screen.findByText(/\/test-skill/i);
    expect(skillName).toBeInTheDocument();
    expect(screen.getByText(/A test skill/i)).toBeInTheDocument();
  });

  test('opens execution dialog when clicking Execute', async () => {
    render(<SkillsManagement />);
    
    const executeBtn = await screen.findByRole('button', { name: /execute/i });
    fireEvent.click(executeBtn);
    
    expect(screen.getByText(/Execute Skill: test-skill/i)).toBeInTheDocument();
  });

  test('starts a skill workflow', async () => {
    render(<SkillsManagement />);
    
    // Open dialog
    const executeBtn = await screen.findByRole('button', { name: /execute/i });
    fireEvent.click(executeBtn);
    
    // Find Execute in dialog
    const startBtn = screen.getByRole('button', { name: /^execute$/i });
    fireEvent.click(startBtn);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/workflow/start-skill'),
        expect.any(Object)
      );
    });
  });
});
