import { Route, Routes } from 'react-router-dom';
import AppShell from './shell/AppShell.jsx';
import { appRoutes } from './routes.jsx';
import { useAuthSession } from '../talons/useAuthSession.js';
import { useCart } from '../talons/useCart.js';
import { useNetworkStatus } from '../talons/useNetworkStatus.js';
import { useProtectedGraphQL } from '../talons/useProtectedGraphQL.js';
import { useTracking } from '../talons/useTracking.js';

export default function App() {
  const auth = useAuthSession();
  const cart = useCart();
  const online = useNetworkStatus();
  const { executeGraphQL } = useProtectedGraphQL(auth.refreshIfNeeded);
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
              element={
                <Page
                  cart={cart}
                  executeGraphQL={executeGraphQL}
                  onTrack={tracking.track}
                />
              }
            />
          );
        })}
      </Route>
    </Routes>
  );
}
