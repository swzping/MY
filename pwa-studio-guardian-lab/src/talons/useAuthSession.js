import { useCallback, useEffect, useState } from 'react';
import { mockGraphQL } from '../graphql/mockClient.js';
import { operations } from '../graphql/operations.js';
import {
  clearAuthSession,
  createDemoSession,
  forceExpireAccess,
  getAuthSession,
  persistRefreshPayload,
  shouldRefreshAccess
} from '../lib/authSession.js';

export function useAuthSession() {
  const [session, setSession] = useState(() => getAuthSession());
  const [message, setMessage] = useState('Session idle');

  const sync = useCallback(() => setSession(getAuthSession()), []);

  const signIn = useCallback(() => {
    createDemoSession();
    setMessage('Demo session created');
    sync();
  }, [sync]);

  const signOut = useCallback(() => {
    clearAuthSession();
    setMessage('Signed out');
    sync();
  }, [sync]);

  const forceExpire = useCallback(() => {
    forceExpireAccess();
    setMessage('Access token forced into expiry window');
    sync();
  }, [sync]);

  const refreshIfNeeded = useCallback(async () => {
    if (!shouldRefreshAccess()) {
      setMessage('Refresh skipped: token is still fresh');
      return;
    }
    const current = getAuthSession();
    const result = await mockGraphQL(operations.refreshCustomerAccessToken, {
      refresh_token: current.refresh_token
    });
    if (result.ok) {
      persistRefreshPayload(result.data.refreshCustomerAccessToken);
      setMessage('Token refreshed before GraphQL operation');
      sync();
    } else {
      setMessage(result.error.message);
    }
  }, [sync]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (shouldRefreshAccess()) {
        refreshIfNeeded();
      }
    }, 3000);
    return () => window.clearInterval(timer);
  }, [refreshIfNeeded]);

  return { session, message, signIn, signOut, forceExpire, refreshIfNeeded };
}
