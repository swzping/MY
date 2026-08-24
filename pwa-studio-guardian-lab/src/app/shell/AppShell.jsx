import { Link, NavLink, Outlet } from 'react-router-dom';
import { appFeatureFlags, appRoutes } from '../routes.jsx';
import StatusPanel from './StatusPanel.jsx';

export default function AppShell({ auth, online, trackingEvents }) {
  return (
    <div className="lab-layout">
      <header className="lab-header">
        <Link className="brand" to="/">Guardian Lab</Link>
        <nav>
          {appRoutes.map(route => (
            <NavLink
              className={route.enabled === false ? 'is-disabled-route' : undefined}
              key={route.path}
              to={route.path}
            >
              {route.name}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="lab-main">
        <Outlet />
      </main>
      <StatusPanel
        auth={auth}
        events={trackingEvents}
        featureFlags={appFeatureFlags}
        online={online}
      />
    </div>
  );
}
