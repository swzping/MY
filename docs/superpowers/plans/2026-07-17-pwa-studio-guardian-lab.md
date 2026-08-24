# PWA Studio Guardian Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `/Users/edy/Documents/MY/pwa-studio-guardian-lab`, a runnable Vite + React learning lab that simulates key Magento PWA Studio/Venia concepts from the Guardian PWA project.

**Architecture:** The app is a local-only React storefront lab. It uses route/payment/feature registries to mimic Buildpack targets, local mock GraphQL functions to mimic Magento GraphQL, talon-style hooks for reusable app logic, and small business modules for commerce, rewards, health, offline events, ads, tracking, and PageBuilder-like content.

**Tech Stack:** Vite, React, React Router, Vitest, Testing Library, localStorage, browser service worker APIs, plain CSS.

---

## File Structure

Create a new project at `/Users/edy/Documents/MY/pwa-studio-guardian-lab`.

```text
pwa-studio-guardian-lab/
  docs/
    learning-map.md
    source-project-notes.md
  public/
    mock-sw.js
  src/
    app/
      App.jsx
      routes.jsx
      shell/AppShell.jsx
      shell/StatusPanel.jsx
    buildpack/
      featureFlags.js
      paymentRegistry.js
      routeRegistry.js
    graphql/
      mockClient.js
      mockData.js
      operations.js
    lib/
      ads.js
      authSession.js
      pwa.js
      tracking.js
    modules/
      account/AccountPage.jsx
      catalog/CatalogPage.jsx
      checkout/CheckoutPage.jsx
      health/HealthPage.jsx
      offlineEvents/OfflineEventsPage.jsx
      pageBuilder/PageBuilderDemo.jsx
      rewards/RewardsPage.jsx
    talons/
      useAuthSession.js
      useCart.js
      useNetworkStatus.js
      useTracking.js
    styles/app.css
    main.jsx
  tests/
    authSession.test.js
    registries.test.js
    mockClient.test.js
  index.html
  package.json
  vite.config.js
  README.md
```

---

### Task 1: Scaffold The Vite React Lab

**Files:**
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/package.json`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/index.html`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/vite.config.js`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/main.jsx`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/app/App.jsx`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/styles/app.css`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/README.md`

- [ ] **Step 1: Create project directory**

Run:

```bash
mkdir -p /Users/edy/Documents/MY/pwa-studio-guardian-lab
```

Expected: directory exists.

- [ ] **Step 2: Write package metadata and scripts**

Create `package.json`:

```json
{
  "name": "pwa-studio-guardian-lab",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "vite build",
    "preview": "vite preview --host 127.0.0.1",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "vite": "^5.4.11",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0"
  },
  "devDependencies": {
    "@testing-library/react": "^16.1.0",
    "@testing-library/jest-dom": "^6.6.3",
    "jsdom": "^25.0.1",
    "vitest": "^2.1.5"
  }
}
```

- [ ] **Step 3: Write Vite config**

Create `vite.config.js`:

```js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true
  }
});
```

- [ ] **Step 4: Write HTML entry**

Create `index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#12312b" />
    <title>PWA Studio Guardian Lab</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 5: Write the initial React entry**

Create `src/main.jsx`:

```jsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './app/App.jsx';
import './styles/app.css';

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
```

- [ ] **Step 6: Write the initial app**

Create `src/app/App.jsx`:

```jsx
export default function App() {
  return (
    <main className="app">
      <section className="hero-panel">
        <p className="eyebrow">Mini PWA Studio Clone</p>
        <h1>Guardian Commerce Lab</h1>
        <p>
          A local learning project for Magento PWA Studio ideas: registries,
          mock GraphQL, talons, PWA status, auth refresh, ads, tracking, and
          business modules.
        </p>
      </section>
    </main>
  );
}
```

- [ ] **Step 7: Write base styles**

Create `src/styles/app.css`:

```css
:root {
  color: #1f2a27;
  background: #f5f2ea;
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 320px;
}

button,
input,
select {
  font: inherit;
}

.app {
  min-height: 100vh;
}

.hero-panel {
  min-height: 100vh;
  display: grid;
  align-content: center;
  gap: 16px;
  padding: clamp(24px, 7vw, 96px);
  background:
    linear-gradient(115deg, rgba(18, 49, 43, 0.92), rgba(18, 49, 43, 0.72)),
    url("https://images.unsplash.com/photo-1556745757-8d76bdb6984b?auto=format&fit=crop&w=1600&q=80");
  background-size: cover;
  background-position: center;
  color: #fffaf0;
}

.eyebrow {
  margin: 0;
  font-size: 0.8rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #f8c95c;
}

h1 {
  margin: 0;
  max-width: 780px;
  font-size: clamp(2.6rem, 8vw, 6.8rem);
  line-height: 0.95;
}

p {
  max-width: 760px;
  line-height: 1.65;
}
```

- [ ] **Step 8: Write README stub**

Create `README.md`:

```markdown
# PWA Studio Guardian Lab

This is a local learning project inspired by a Magento PWA Studio Guardian storefront.

It teaches:

- PWA Studio style app structure
- Buildpack-like registries
- Peregrine-style talons/hooks
- mock GraphQL data flow
- OAuth/customer token refresh
- PWA online/offline behavior
- commerce, rewards, health, offline event, ad, and tracking modules

Run it with:

```bash
npm install
npm run dev
```
```

- [ ] **Step 9: Install dependencies**

Run:

```bash
cd /Users/edy/Documents/MY/pwa-studio-guardian-lab
npm install
```

Expected: `node_modules` and `package-lock.json` are created.

- [ ] **Step 10: Verify the scaffold builds**

Run:

```bash
cd /Users/edy/Documents/MY/pwa-studio-guardian-lab
npm run build
```

Expected: Vite build succeeds and creates `dist/`.

- [ ] **Step 11: Commit**

Run:

```bash
cd /Users/edy/Documents/MY
git add pwa-studio-guardian-lab
git commit -m "feat: scaffold pwa studio guardian lab"
```

Expected: one commit containing the initial learning project scaffold.

---

### Task 2: Add Buildpack-Style Registries

**Files:**
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/buildpack/featureFlags.js`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/buildpack/routeRegistry.js`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/buildpack/paymentRegistry.js`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/tests/registries.test.js`

- [ ] **Step 1: Write failing registry tests**

Create `tests/registries.test.js`:

```js
import { describe, expect, it } from 'vitest';
import { featureFlags, isFeatureEnabled } from '../src/buildpack/featureFlags.js';
import { createRouteRegistry } from '../src/buildpack/routeRegistry.js';
import { createPaymentRegistry } from '../src/buildpack/paymentRegistry.js';

describe('buildpack-style registries', () => {
  it('reads feature flags by key', () => {
    expect(featureFlags.health).toBe(true);
    expect(isFeatureEnabled('offlineEvents')).toBe(true);
    expect(isFeatureEnabled('missingFeature')).toBe(false);
  });

  it('registers routes in insertion order', () => {
    const registry = createRouteRegistry();
    registry.add({ name: 'home', path: '/', module: 'catalog' });
    registry.add({ name: 'rewards', path: '/rewards', module: 'rewards' });
    expect(registry.list().map(route => route.name)).toEqual(['home', 'rewards']);
  });

  it('prevents duplicate payment codes', () => {
    const registry = createPaymentRegistry();
    registry.add({ code: 'snap', title: 'Snap Demo' });
    expect(() => registry.add({ code: 'snap', title: 'Duplicate' })).toThrow(
      'Payment method already registered: snap'
    );
  });
});
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd /Users/edy/Documents/MY/pwa-studio-guardian-lab
npm test -- registries.test.js
```

Expected: FAIL because registry modules do not exist.

- [ ] **Step 3: Implement feature flags**

Create `src/buildpack/featureFlags.js`:

```js
export const featureFlags = {
  ads: true,
  checkout: true,
  health: true,
  offlineEvents: true,
  rewards: true,
  tracking: true
};

export function isFeatureEnabled(key) {
  return featureFlags[key] === true;
}
```

- [ ] **Step 4: Implement route registry**

Create `src/buildpack/routeRegistry.js`:

```js
export function createRouteRegistry() {
  const routes = [];

  return {
    add(route) {
      if (!route?.name || !route?.path || !route?.module) {
        throw new Error('Route requires name, path, and module');
      }
      if (routes.some(existing => existing.name === route.name)) {
        throw new Error(`Route already registered: ${route.name}`);
      }
      routes.push(route);
    },
    list() {
      return [...routes];
    }
  };
}

export const routeRegistry = createRouteRegistry();
```

- [ ] **Step 5: Implement payment registry**

Create `src/buildpack/paymentRegistry.js`:

```js
export function createPaymentRegistry() {
  const methods = [];

  return {
    add(method) {
      if (!method?.code || !method?.title) {
        throw new Error('Payment method requires code and title');
      }
      if (methods.some(existing => existing.code === method.code)) {
        throw new Error(`Payment method already registered: ${method.code}`);
      }
      methods.push(method);
    },
    list() {
      return [...methods];
    }
  };
}

export const paymentRegistry = createPaymentRegistry();
```

- [ ] **Step 6: Verify registry tests pass**

Run:

```bash
cd /Users/edy/Documents/MY/pwa-studio-guardian-lab
npm test -- registries.test.js
```

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```bash
cd /Users/edy/Documents/MY
git add pwa-studio-guardian-lab/src/buildpack pwa-studio-guardian-lab/tests/registries.test.js
git commit -m "feat: add pwa studio style registries"
```

---

### Task 3: Add Mock GraphQL Layer

**Files:**
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/graphql/mockData.js`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/graphql/operations.js`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/graphql/mockClient.js`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/tests/mockClient.test.js`

- [ ] **Step 1: Write failing mock GraphQL tests**

Create `tests/mockClient.test.js`:

```js
import { describe, expect, it } from 'vitest';
import { mockGraphQL } from '../src/graphql/mockClient.js';

describe('mockGraphQL', () => {
  it('returns products for GetProducts', async () => {
    const result = await mockGraphQL('GetProducts');
    expect(result.ok).toBe(true);
    expect(result.data.products.length).toBeGreaterThan(1);
  });

  it('returns token refresh payload', async () => {
    const result = await mockGraphQL('RefreshCustomerAccessToken', {
      refresh_token: 'refresh-demo'
    });
    expect(result.ok).toBe(true);
    expect(result.data.refreshCustomerAccessToken.customer_token.token).toContain(
      'customer-token'
    );
  });

  it('returns structured errors for unknown operations', async () => {
    const result = await mockGraphQL('UnknownOperation');
    expect(result.ok).toBe(false);
    expect(result.error.message).toBe('Unknown mock operation: UnknownOperation');
  });
});
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd /Users/edy/Documents/MY/pwa-studio-guardian-lab
npm test -- mockClient.test.js
```

Expected: FAIL because mock GraphQL files do not exist.

- [ ] **Step 3: Create mock data**

Create `src/graphql/mockData.js`:

```js
export const mockData = {
  products: [
    { id: 'sku-001', name: 'Daily Shield Sunscreen', price: 89000, category: 'Skin Care' },
    { id: 'sku-002', name: 'Vitamin C Bright Serum', price: 129000, category: 'Skin Care' },
    { id: 'sku-003', name: 'Family Health Test Kit', price: 249000, category: 'Health' }
  ],
  customer: {
    id: 'member-1001',
    name: 'Guardian Learner',
    email: 'learner@example.test',
    points: 1280,
    storeCredit: 75000
  },
  orders: [
    { id: 'ORD-9001', status: 'Delivered', total: 318000 },
    { id: 'ORD-9002', status: 'On the road', total: 129000 }
  ],
  coupons: [
    { code: 'HEALTH10', label: '10% health service discount' },
    { code: 'GIFTREADY', label: 'Free gift unlocked' }
  ],
  healthRecords: [
    { id: 'health-1', title: 'Apoteker consultation', status: 'Completed' },
    { id: 'health-2', title: 'Medical test result', status: 'Ready' }
  ],
  events: [
    { id: 'event-1', title: 'Skin Care Class', seats: 12 },
    { id: 'event-2', title: 'Family Health Weekend', seats: 8 }
  ]
};
```

- [ ] **Step 4: Create operation names**

Create `src/graphql/operations.js`:

```js
export const operations = {
  getProducts: 'GetProducts',
  getCustomerDashboard: 'GetCustomerDashboard',
  getBusinessModules: 'GetBusinessModules',
  refreshCustomerAccessToken: 'RefreshCustomerAccessToken'
};
```

- [ ] **Step 5: Implement mock GraphQL client**

Create `src/graphql/mockClient.js`:

```js
import { mockData } from './mockData.js';
import { operations } from './operations.js';

function createTokenPayload(refreshToken) {
  const suffix = String(Date.now()).slice(-5);
  return {
    status: true,
    message: 'refreshed',
    access_token: `access-token-${suffix}`,
    refresh_token: refreshToken || `refresh-token-${suffix}`,
    expires_in: 3600,
    customer_token: {
      token: `customer-token-${suffix}`
    }
  };
}

export async function mockGraphQL(operationName, variables = {}) {
  await new Promise(resolve => setTimeout(resolve, 80));

  switch (operationName) {
    case operations.getProducts:
      return { ok: true, data: { products: mockData.products } };
    case operations.getCustomerDashboard:
      return {
        ok: true,
        data: {
          customer: mockData.customer,
          orders: mockData.orders,
          coupons: mockData.coupons
        }
      };
    case operations.getBusinessModules:
      return {
        ok: true,
        data: {
          healthRecords: mockData.healthRecords,
          events: mockData.events
        }
      };
    case operations.refreshCustomerAccessToken:
      return {
        ok: true,
        data: {
          refreshCustomerAccessToken: createTokenPayload(variables.refresh_token)
        }
      };
    default:
      return {
        ok: false,
        error: { message: `Unknown mock operation: ${operationName}` }
      };
  }
}
```

- [ ] **Step 6: Verify mock GraphQL tests pass**

Run:

```bash
cd /Users/edy/Documents/MY/pwa-studio-guardian-lab
npm test -- mockClient.test.js
```

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```bash
cd /Users/edy/Documents/MY
git add pwa-studio-guardian-lab/src/graphql pwa-studio-guardian-lab/tests/mockClient.test.js
git commit -m "feat: add local mock graphql layer"
```

---

### Task 4: Add Auth Refresh And Talons

**Files:**
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/lib/authSession.js`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/talons/useAuthSession.js`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/talons/useNetworkStatus.js`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/talons/useCart.js`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/tests/authSession.test.js`

- [ ] **Step 1: Write failing auth session tests**

Create `tests/authSession.test.js`:

```js
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  clearAuthSession,
  createDemoSession,
  getAuthSession,
  shouldRefreshAccess,
  forceExpireAccess
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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd /Users/edy/Documents/MY/pwa-studio-guardian-lab
npm test -- authSession.test.js
```

Expected: FAIL because `authSession.js` does not exist.

- [ ] **Step 3: Implement auth session utilities**

Create `src/lib/authSession.js`:

```js
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
```

- [ ] **Step 4: Create auth talon**

Create `src/talons/useAuthSession.js`:

```jsx
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
```

- [ ] **Step 5: Create network talon**

Create `src/talons/useNetworkStatus.js`:

```jsx
import { useEffect, useState } from 'react';

export function useNetworkStatus() {
  const [online, setOnline] = useState(() => navigator.onLine);

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }, []);

  return online;
}
```

- [ ] **Step 6: Create cart talon**

Create `src/talons/useCart.js`:

```jsx
import { useMemo, useState } from 'react';

export function useCart() {
  const [items, setItems] = useState([]);

  const addItem = product => {
    setItems(current => [...current, { ...product, quantity: 1 }]);
  };

  const total = useMemo(
    () => items.reduce((sum, item) => sum + item.price * item.quantity, 0),
    [items]
  );

  return { items, addItem, total };
}
```

- [ ] **Step 7: Verify auth tests pass**

Run:

```bash
cd /Users/edy/Documents/MY/pwa-studio-guardian-lab
npm test -- authSession.test.js
```

Expected: PASS.

- [ ] **Step 8: Commit**

Run:

```bash
cd /Users/edy/Documents/MY
git add pwa-studio-guardian-lab/src/lib/authSession.js pwa-studio-guardian-lab/src/talons pwa-studio-guardian-lab/tests/authSession.test.js
git commit -m "feat: add auth refresh lab talons"
```

---

### Task 5: Build App Shell, Routes, And Business Pages

**Files:**
- Modify: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/app/App.jsx`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/app/routes.jsx`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/app/shell/AppShell.jsx`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/app/shell/StatusPanel.jsx`
- Create: all module page files under `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/modules/`
- Modify: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/styles/app.css`

- [ ] **Step 1: Create module pages**

Create these files with focused page components:

`src/modules/catalog/CatalogPage.jsx`:

```jsx
import { useEffect, useState } from 'react';
import { mockGraphQL } from '../../graphql/mockClient.js';
import { operations } from '../../graphql/operations.js';

export default function CatalogPage({ onTrack }) {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    mockGraphQL(operations.getProducts).then(result => {
      if (result.ok) setProducts(result.data.products);
    });
  }, []);

  return (
    <section className="page-grid">
      <div>
        <p className="eyebrow">Catalog</p>
        <h2>Mock Magento Product Grid</h2>
        <p>Products come from the local mock GraphQL client.</p>
      </div>
      <div className="cards-grid">
        {products.map(product => (
          <article className="lab-card" key={product.id}>
            <span>{product.category}</span>
            <h3>{product.name}</h3>
            <p>IDR {product.price.toLocaleString('id-ID')}</p>
            <button onClick={() => onTrack('product_click', product.id)}>Track click</button>
          </article>
        ))}
      </div>
    </section>
  );
}
```

`src/modules/account/AccountPage.jsx`:

```jsx
import { useEffect, useState } from 'react';
import { mockGraphQL } from '../../graphql/mockClient.js';
import { operations } from '../../graphql/operations.js';

export default function AccountPage() {
  const [dashboard, setDashboard] = useState(null);

  useEffect(() => {
    mockGraphQL(operations.getCustomerDashboard).then(result => {
      if (result.ok) setDashboard(result.data);
    });
  }, []);

  if (!dashboard) return <p>Loading account dashboard...</p>;

  return (
    <section className="page-grid">
      <div>
        <p className="eyebrow">Account</p>
        <h2>{dashboard.customer.name}</h2>
        <p>{dashboard.customer.email}</p>
      </div>
      <div className="cards-grid">
        {dashboard.orders.map(order => (
          <article className="lab-card" key={order.id}>
            <span>{order.status}</span>
            <h3>{order.id}</h3>
            <p>IDR {order.total.toLocaleString('id-ID')}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
```

`src/modules/rewards/RewardsPage.jsx`:

```jsx
import { mockData } from '../../graphql/mockData.js';

export default function RewardsPage() {
  return (
    <section className="page-grid">
      <div>
        <p className="eyebrow">Rewards</p>
        <h2>Points, coupons, and store credit</h2>
        <p>This mirrors the Guardian project's reward points, coupons, and store credit surfaces.</p>
      </div>
      <div className="cards-grid">
        <article className="lab-card"><span>Points</span><h3>{mockData.customer.points}</h3></article>
        <article className="lab-card"><span>Store Credit</span><h3>IDR {mockData.customer.storeCredit.toLocaleString('id-ID')}</h3></article>
        {mockData.coupons.map(coupon => (
          <article className="lab-card" key={coupon.code}><span>{coupon.code}</span><h3>{coupon.label}</h3></article>
        ))}
      </div>
    </section>
  );
}
```

`src/modules/health/HealthPage.jsx`:

```jsx
import { mockData } from '../../graphql/mockData.js';

export default function HealthPage() {
  return (
    <section className="page-grid">
      <div>
        <p className="eyebrow">Health</p>
        <h2>Apoteker and medical service lab</h2>
        <p>Shows how non-commerce service flows can live beside a storefront.</p>
      </div>
      <div className="cards-grid">
        {mockData.healthRecords.map(record => (
          <article className="lab-card" key={record.id}>
            <span>{record.status}</span>
            <h3>{record.title}</h3>
          </article>
        ))}
      </div>
    </section>
  );
}
```

`src/modules/offlineEvents/OfflineEventsPage.jsx`:

```jsx
import { mockData } from '../../graphql/mockData.js';

export default function OfflineEventsPage() {
  return (
    <section className="page-grid">
      <div>
        <p className="eyebrow">Offline Events</p>
        <h2>Booking and ticket concepts</h2>
        <p>Inspired by offline event booking, activity forms, and ticket list routes.</p>
      </div>
      <div className="cards-grid">
        {mockData.events.map(event => (
          <article className="lab-card" key={event.id}>
            <span>{event.seats} seats</span>
            <h3>{event.title}</h3>
            <button>Register demo</button>
          </article>
        ))}
      </div>
    </section>
  );
}
```

`src/modules/checkout/CheckoutPage.jsx`:

```jsx
import { paymentRegistry } from '../../buildpack/paymentRegistry.js';

const methods = [
  { code: 'snap', title: 'Midtrans Snap Demo' },
  { code: 'snap_gopay', title: 'GoPay Demo' },
  { code: 'banktransfer', title: 'Bank Transfer Demo' }
];

for (const method of methods) {
  try {
    paymentRegistry.add(method);
  } catch {
    // StrictMode may import twice in development.
  }
}

export default function CheckoutPage() {
  return (
    <section className="page-grid">
      <div>
        <p className="eyebrow">Checkout</p>
        <h2>Payment registry demo</h2>
        <p>Payment methods are registered by code, like PWA Studio checkout payment targets.</p>
      </div>
      <div className="cards-grid">
        {paymentRegistry.list().map(method => (
          <article className="lab-card" key={method.code}>
            <span>{method.code}</span>
            <h3>{method.title}</h3>
          </article>
        ))}
      </div>
    </section>
  );
}
```

`src/modules/pageBuilder/PageBuilderDemo.jsx`:

```jsx
export default function PageBuilderDemo({ onTrack }) {
  return (
    <section className="page-builder-demo">
      <div>
        <p className="eyebrow">PageBuilder + Ads</p>
        <h2>Campaign banner simulation</h2>
        <p>Lazy content, ad slot metadata, and click tracking in one teaching surface.</p>
        <button onClick={() => onTrack('banner_click', 'home-hero-ad')}>Track banner click</button>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Create routes**

Create `src/app/routes.jsx`:

```jsx
import AccountPage from '../modules/account/AccountPage.jsx';
import CatalogPage from '../modules/catalog/CatalogPage.jsx';
import CheckoutPage from '../modules/checkout/CheckoutPage.jsx';
import HealthPage from '../modules/health/HealthPage.jsx';
import OfflineEventsPage from '../modules/offlineEvents/OfflineEventsPage.jsx';
import PageBuilderDemo from '../modules/pageBuilder/PageBuilderDemo.jsx';
import RewardsPage from '../modules/rewards/RewardsPage.jsx';

export const appRoutes = [
  { name: 'Catalog', path: '/', element: CatalogPage },
  { name: 'Account', path: '/account', element: AccountPage },
  { name: 'Checkout', path: '/checkout', element: CheckoutPage },
  { name: 'Rewards', path: '/rewards', element: RewardsPage },
  { name: 'Health', path: '/health', element: HealthPage },
  { name: 'Offline Events', path: '/offline-events', element: OfflineEventsPage },
  { name: 'PageBuilder', path: '/pagebuilder', element: PageBuilderDemo }
];
```

- [ ] **Step 3: Create status panel**

Create `src/app/shell/StatusPanel.jsx`:

```jsx
export default function StatusPanel({ auth, online, events }) {
  return (
    <aside className="status-panel">
      <h2>Lab Status</h2>
      <p><strong>Network:</strong> {online ? 'online' : 'offline'}</p>
      <p><strong>Signin token:</strong> {auth.session.signin_token || 'none'}</p>
      <p><strong>Auth message:</strong> {auth.message}</p>
      <div className="button-row">
        <button onClick={auth.signIn}>Sign in</button>
        <button onClick={auth.forceExpire}>Force expire</button>
        <button onClick={auth.refreshIfNeeded}>Refresh if needed</button>
        <button onClick={auth.signOut}>Sign out</button>
      </div>
      <h3>Tracking Log</h3>
      <ul className="event-log">
        {events.slice(-6).map(event => (
          <li key={event.id}>{event.type}: {event.label}</li>
        ))}
      </ul>
    </aside>
  );
}
```

- [ ] **Step 4: Create app shell**

Create `src/app/shell/AppShell.jsx`:

```jsx
import { Link, NavLink, Outlet } from 'react-router-dom';
import { appRoutes } from '../routes.jsx';
import StatusPanel from './StatusPanel.jsx';

export default function AppShell({ auth, online, trackingEvents }) {
  return (
    <div className="lab-layout">
      <header className="lab-header">
        <Link className="brand" to="/">Guardian Lab</Link>
        <nav>
          {appRoutes.map(route => (
            <NavLink key={route.path} to={route.path}>
              {route.name}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="lab-main">
        <Outlet />
      </main>
      <StatusPanel auth={auth} online={online} events={trackingEvents} />
    </div>
  );
}
```

- [ ] **Step 5: Update App**

Replace `src/app/App.jsx` with:

```jsx
import { Route, Routes } from 'react-router-dom';
import AppShell from './shell/AppShell.jsx';
import { appRoutes } from './routes.jsx';
import { useAuthSession } from '../talons/useAuthSession.js';
import { useNetworkStatus } from '../talons/useNetworkStatus.js';
import { useTracking } from '../talons/useTracking.js';

export default function App() {
  const auth = useAuthSession();
  const online = useNetworkStatus();
  const tracking = useTracking();

  return (
    <Routes>
      <Route
        element={
          <AppShell auth={auth} online={online} trackingEvents={tracking.events} />
        }
      >
        {appRoutes.map(route => {
          const Page = route.element;
          return (
            <Route
              key={route.path}
              path={route.path}
              element={<Page onTrack={tracking.track} />}
            />
          );
        })}
      </Route>
    </Routes>
  );
}
```

- [ ] **Step 6: Add tracking talon**

Create `src/talons/useTracking.js`:

```jsx
import { useCallback, useState } from 'react';

export function useTracking() {
  const [events, setEvents] = useState([]);

  const track = useCallback((type, label) => {
    setEvents(current => [
      ...current,
      { id: `${Date.now()}-${current.length}`, type, label }
    ]);
  }, []);

  return { events, track };
}
```

- [ ] **Step 7: Replace styles**

Replace `src/styles/app.css` with a complete layout stylesheet:

```css
:root {
  color: #20312d;
  background: #f4efe4;
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* { box-sizing: border-box; }
body { margin: 0; min-width: 320px; }
button, input, select { font: inherit; }
button {
  border: 1px solid #c9a94f;
  background: #f7ce62;
  color: #1f2a27;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
}

.lab-layout {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  grid-template-rows: auto 1fr;
}

.lab-header {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  gap: 22px;
  padding: 14px 22px;
  background: #12312b;
  color: #fff7e6;
  border-bottom: 4px solid #f7ce62;
}

.brand {
  color: inherit;
  font-weight: 800;
  text-decoration: none;
  white-space: nowrap;
}

.lab-header nav {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.lab-header nav a {
  color: #fff7e6;
  text-decoration: none;
  padding: 7px 9px;
  border-radius: 6px;
}

.lab-header nav a.active {
  background: rgba(247, 206, 98, 0.22);
}

.lab-main {
  padding: clamp(20px, 4vw, 54px);
}

.status-panel {
  border-left: 1px solid #ddd0b5;
  background: #fffaf0;
  padding: 24px;
}

.button-row {
  display: grid;
  gap: 8px;
}

.event-log {
  padding-left: 18px;
  line-height: 1.6;
}

.page-grid {
  display: grid;
  gap: 28px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #9c6b00;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 800;
}

h2 {
  margin: 0;
  font-size: clamp(2rem, 5vw, 4.5rem);
  line-height: 1;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.lab-card {
  background: #fffaf0;
  border: 1px solid #ddd0b5;
  border-radius: 8px;
  padding: 18px;
}

.lab-card span {
  color: #8f6b1d;
  font-weight: 800;
  font-size: 0.78rem;
}

.page-builder-demo {
  min-height: 480px;
  display: grid;
  align-content: end;
  padding: clamp(24px, 6vw, 72px);
  color: #fffaf0;
  background:
    linear-gradient(100deg, rgba(18, 49, 43, 0.9), rgba(18, 49, 43, 0.2)),
    url("https://images.unsplash.com/photo-1606813907291-d86efa9b94db?auto=format&fit=crop&w=1600&q=80");
  background-size: cover;
  background-position: center;
}

@media (max-width: 980px) {
  .lab-layout {
    grid-template-columns: 1fr;
  }

  .status-panel {
    border-left: 0;
    border-top: 1px solid #ddd0b5;
  }
}
```

- [ ] **Step 8: Verify app builds**

Run:

```bash
cd /Users/edy/Documents/MY/pwa-studio-guardian-lab
npm run build
```

Expected: PASS.

- [ ] **Step 9: Commit**

Run:

```bash
cd /Users/edy/Documents/MY
git add pwa-studio-guardian-lab/src
git commit -m "feat: build guardian lab shell and modules"
```

---

### Task 6: Add PWA Registration, Ads Helpers, And Documentation

**Files:**
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/public/mock-sw.js`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/lib/pwa.js`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/lib/ads.js`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/lib/tracking.js`
- Modify: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/src/main.jsx`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/docs/learning-map.md`
- Create: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/docs/source-project-notes.md`
- Modify: `/Users/edy/Documents/MY/pwa-studio-guardian-lab/README.md`

- [ ] **Step 1: Create service worker**

Create `public/mock-sw.js`:

```js
self.addEventListener('install', event => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', () => {
  // Learning lab only: no production caching strategy in v1.
});
```

- [ ] **Step 2: Create PWA registration helper**

Create `src/lib/pwa.js`:

```js
export function registerMockServiceWorker() {
  if (!('serviceWorker' in navigator)) {
    return Promise.resolve('service worker unavailable');
  }
  return navigator.serviceWorker
    .register('/mock-sw.js')
    .then(() => 'mock service worker registered')
    .catch(error => `mock service worker failed: ${error.message}`);
}
```

- [ ] **Step 3: Create ads helper**

Create `src/lib/ads.js`:

```js
export const OSMOS_H5_MAX_WIDTH = 767;

export function isH5(width = window.innerWidth) {
  return width <= OSMOS_H5_MAX_WIDTH;
}

export function getHomeAdConfig(slot, width = window.innerWidth) {
  const prefix = isH5(width) ? 'GUIDMWeb' : 'GUIDDWeb';
  return {
    pageType: `${prefix}HomePage`,
    adUnit: [`${prefix}${slot}`]
  };
}

export function createAdPool(ads) {
  let index = 0;
  return {
    consume() {
      const ad = ads[index] || null;
      index += 1;
      return ad;
    },
    reset() {
      index = 0;
    }
  };
}
```

- [ ] **Step 4: Create tracking helper**

Create `src/lib/tracking.js`:

```js
export function createTrackingEvent(type, label) {
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    type,
    label,
    createdAt: new Date().toISOString()
  };
}
```

- [ ] **Step 5: Register service worker from entry**

Modify `src/main.jsx`:

```jsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './app/App.jsx';
import { registerMockServiceWorker } from './lib/pwa.js';
import './styles/app.css';

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);

registerMockServiceWorker().then(message => {
  console.info(`[PWA Lab] ${message}`);
});
```

- [ ] **Step 6: Write learning map**

Create `docs/learning-map.md`:

```markdown
# Learning Map

## What This Lab Teaches

- `src/buildpack/*`: how PWA Studio target-like registries can register routes, feature flags, and payment methods.
- `src/graphql/*`: how the UI can depend on GraphQL-style operations without a real backend.
- `src/lib/authSession.js`: why the Guardian project needed a dual OAuth and Magento customer token model.
- `src/talons/*`: how Peregrine-style talons separate app logic from UI.
- `src/modules/*`: how commerce and non-commerce business flows can coexist in one storefront.
- `public/mock-sw.js`: where PWA service worker behavior starts.

## Suggested Study Order

1. Run the app.
2. Open the status panel and create a demo session.
3. Force token expiry and refresh it.
4. Navigate Catalog, Account, Rewards, Health, Offline Events, Checkout, and PageBuilder.
5. Read each source file in the same order as the UI.
```

- [ ] **Step 7: Write source notes**

Create `docs/source-project-notes.md`:

```markdown
# Source Project Notes

This lab is inspired by the Guardian Magento PWA project.

Mapped concepts:

- Magento PWA Studio / Venia shell -> `src/app`
- PWA Buildpack targets -> `src/buildpack`
- Peregrine talons -> `src/talons`
- Magento GraphQL -> `src/graphql`
- OAuth refresh link -> `src/lib/authSession.js`
- Online/offline PWA behavior -> `src/lib/pwa.js` and `useNetworkStatus`
- Midtrans/payment registration -> `paymentRegistry`
- Rewards, store credit, coupons -> `RewardsPage`
- Apoteker and medical pages -> `HealthPage`
- Offline event booking -> `OfflineEventsPage`
- PageBuilder banners, ads, tracking -> `PageBuilderDemo`, `ads.js`, and `useTracking`

The lab intentionally uses mock data and original teaching code. It does not copy the production storefront.
```

- [ ] **Step 8: Expand README**

Replace `README.md` with:

```markdown
# PWA Studio Guardian Lab

A local learning project inspired by a Magento PWA Studio Guardian storefront.

## Run

```bash
npm install
npm run dev
```

## Build And Test

```bash
npm test
npm run build
```

## What To Study

- `docs/learning-map.md`
- `docs/source-project-notes.md`
- `src/buildpack`
- `src/graphql`
- `src/lib/authSession.js`
- `src/talons`
- `src/modules`

## Why This Exists

The original project is a large Magento PWA Studio storefront. This lab extracts the learning value into a small app you can run locally without Magento, payment credentials, or production APIs.
```

- [ ] **Step 9: Verify tests and build**

Run:

```bash
cd /Users/edy/Documents/MY/pwa-studio-guardian-lab
npm test
npm run build
```

Expected: all tests pass and build succeeds.

- [ ] **Step 10: Start dev server and inspect**

Run:

```bash
cd /Users/edy/Documents/MY/pwa-studio-guardian-lab
npm run dev
```

Expected: Vite prints a local URL. Open the URL and verify navigation, auth buttons, tracking events, and responsive layout.

- [ ] **Step 11: Commit**

Run:

```bash
cd /Users/edy/Documents/MY
git add pwa-studio-guardian-lab
git commit -m "docs: finish pwa guardian lab learning guide"
```

---

## Final Verification

- [ ] Run all tests:

```bash
cd /Users/edy/Documents/MY/pwa-studio-guardian-lab
npm test
```

Expected: PASS.

- [ ] Run production build:

```bash
cd /Users/edy/Documents/MY/pwa-studio-guardian-lab
npm run build
```

Expected: PASS.

- [ ] Start local server:

```bash
cd /Users/edy/Documents/MY/pwa-studio-guardian-lab
npm run dev
```

Expected: local Vite URL is available for user review.

- [ ] Manual review:

Check these flows in browser:

- Demo sign in creates tokens.
- Force expire changes refresh state.
- Refresh if needed updates the `signin_token`.
- Catalog loads mock products.
- Account loads mock customer data.
- Checkout lists registered payment methods.
- Rewards, Health, Offline Events, and PageBuilder pages render.
- Tracking log updates after product and banner clicks.

