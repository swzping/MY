import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  clearAuthSession,
  createDemoSession,
  forceExpireAccess,
  getAuthSession,
  shouldRefreshAccess
} from '../src/lib/authSession.js';

describe('auth session lab', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useRealTimers();
  });

  it('creates a dual token demo session', () => {
    createDemoSession();
    const session = getAuthSession();
    expect(session.access_token).toContain('access-token');
    expect(session.refresh_token).toContain('refresh-token');
    expect(session.signin_token).toContain('customer-token');
  });

  it('detects near-expiry access tokens', () => {
    createDemoSession();
    expect(shouldRefreshAccess()).toBe(false);
    forceExpireAccess();
    expect(shouldRefreshAccess()).toBe(true);
  });

  it('clears all auth keys', () => {
    createDemoSession();
    clearAuthSession();
    expect(getAuthSession().signin_token).toBe('');
  });
});
