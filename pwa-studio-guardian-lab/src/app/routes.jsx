import { featureFlags, isFeatureEnabled } from '../buildpack/featureFlags.js';
import { routeRegistry } from '../buildpack/routeRegistry.js';
import AccountPage from '../modules/account/AccountPage.jsx';
import CatalogPage from '../modules/catalog/CatalogPage.jsx';
import CheckoutPage from '../modules/checkout/CheckoutPage.jsx';
import HealthPage from '../modules/health/HealthPage.jsx';
import OfflineEventsPage from '../modules/offlineEvents/OfflineEventsPage.jsx';
import PageBuilderDemo from '../modules/pageBuilder/PageBuilderDemo.jsx';
import RewardsPage from '../modules/rewards/RewardsPage.jsx';

export function ModuleDisabledPage({ routeName, feature }) {
  return (
    <section className="page-grid">
      <div>
        <p className="eyebrow">Feature Flag</p>
        <h2>{routeName} is disabled</h2>
        <p>The {feature} feature flag is off, so this module is hidden by the route registry.</p>
      </div>
    </section>
  );
}

function registerRoute(route) {
  const enabled = route.feature ? isFeatureEnabled(route.feature) : true;

  routeRegistry.upsert({
    ...route,
    enabled,
    element: enabled
      ? route.element
      : props => (
          <ModuleDisabledPage
            {...props}
            routeName={route.name}
            feature={route.feature}
          />
        )
  });
}

[
  { name: 'Catalog', path: '/', element: CatalogPage },
  { name: 'Account', path: '/account', element: AccountPage },
  { name: 'Checkout', path: '/checkout', element: CheckoutPage, feature: 'checkout' },
  { name: 'Rewards', path: '/rewards', element: RewardsPage, feature: 'rewards' },
  { name: 'Health', path: '/health', element: HealthPage, feature: 'health' },
  {
    name: 'Offline Events',
    path: '/offline-events',
    element: OfflineEventsPage,
    feature: 'offlineEvents'
  },
  { name: 'PageBuilder', path: '/pagebuilder', element: PageBuilderDemo, feature: 'ads' }
].forEach(registerRoute);

export const appRoutes = routeRegistry.list();
export const appFeatureFlags = featureFlags;
