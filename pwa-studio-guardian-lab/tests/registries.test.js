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
    registry.add({ name: 'home', path: '/', element: () => null });
    registry.add({ name: 'rewards', path: '/rewards', element: () => null });
    expect(registry.list().map(route => route.name)).toEqual(['home', 'rewards']);
  });

  it('upserts routes for dev-time re-registration', () => {
    const registry = createRouteRegistry();
    const First = () => null;
    const Second = () => null;

    registry.upsert({ name: 'home', path: '/', element: First });
    registry.upsert({ name: 'home', path: '/', element: Second });

    expect(registry.list()).toHaveLength(1);
    expect(registry.list()[0].element).toBe(Second);
  });

  it('exposes registered app routes with feature enabled state', async () => {
    const { appRoutes } = await import('../src/app/routes.jsx');
    const rewardsRoute = appRoutes.find(route => route.path === '/rewards');

    expect(appRoutes.length).toBeGreaterThan(1);
    expect(rewardsRoute.feature).toBe('rewards');
    expect(rewardsRoute.enabled).toBe(true);
    expect(rewardsRoute.element).toBeTypeOf('function');
  });

  it('prevents duplicate payment codes', () => {
    const registry = createPaymentRegistry();
    registry.add({ code: 'snap', title: 'Snap Demo' });
    expect(() => registry.add({ code: 'snap', title: 'Duplicate' })).toThrow(
      'Payment method already registered: snap'
    );
  });
});
