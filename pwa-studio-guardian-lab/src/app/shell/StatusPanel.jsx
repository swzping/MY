export default function StatusPanel({ auth, online, events, featureFlags }) {
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
      <h3>Feature Flags</h3>
      <ul className="feature-list">
        {Object.entries(featureFlags).map(([key, enabled]) => (
          <li key={key}>
            <span>{key}</span>
            <strong>{enabled ? 'on' : 'off'}</strong>
          </li>
        ))}
      </ul>
      <h3>Tracking Log</h3>
      <ul className="event-log">
        {events.slice(-6).map(event => (
          <li key={event.id}>{event.type}: {event.label}</li>
        ))}
      </ul>
    </aside>
  );
}
