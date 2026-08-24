const AUTH_KEYS = [
  'access_token',
  'refresh_token',
  'access_token_expires_at',
  'customer_token',
  'signin_token'
];

export const REFRESH_BEFORE_EXPIRY_MS = 5 * 60 * 1000;

function setItem(key, value) {
  localStorage.setItem(key, value);
}

export function createDemoSession() {
  const suffix = String(Date.now()).slice(-5);
  const expiresAt = Date.now() + 60 * 60 * 1000;
  setItem('access_token', `access-token-${suffix}`);
  setItem('refresh_token', `refresh-token-${suffix}`);
  setItem('access_token_expires_at', String(expiresAt));
  setItem('customer_token', JSON.stringify({ token: `customer-token-${suffix}` }));
  setItem('signin_token', `customer-token-${suffix}`);
}

export function getAuthSession() {
  return {
    access_token: localStorage.getItem('access_token') || '',
    refresh_token: localStorage.getItem('refresh_token') || '',
    access_token_expires_at: Number(localStorage.getItem('access_token_expires_at') || 0),
    customer_token: localStorage.getItem('customer_token') || '',
    signin_token: localStorage.getItem('signin_token') || ''
  };
}

export function shouldRefreshAccess(bufferMs = REFRESH_BEFORE_EXPIRY_MS) {
  const session = getAuthSession();
  if (!session.refresh_token || !session.access_token_expires_at) {
    return false;
  }
  return Date.now() + bufferMs >= session.access_token_expires_at;
}

export function persistRefreshPayload(payload) {
  if (payload.access_token) setItem('access_token', payload.access_token);
  if (payload.refresh_token) setItem('refresh_token', payload.refresh_token);
  if (payload.expires_in) {
    setItem('access_token_expires_at', String(Date.now() + payload.expires_in * 1000));
  }
  if (payload.customer_token) {
    setItem('customer_token', JSON.stringify(payload.customer_token));
    setItem('signin_token', payload.customer_token.token);
  }
}

export function forceExpireAccess() {
  setItem('access_token_expires_at', String(Date.now() - 1000));
}

export function clearAuthSession() {
  for (const key of AUTH_KEYS) {
    localStorage.removeItem(key);
  }
}
