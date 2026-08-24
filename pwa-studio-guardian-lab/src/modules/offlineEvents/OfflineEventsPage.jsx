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
      <section>
        <p className="eyebrow">Ticket List</p>
        <div className="cards-grid">
          {mockData.events.map(event => (
            <article className="lab-card" key={`${event.id}-ticket`}>
              <span>Ticket #{event.id}</span>
              <h3>{event.title}</h3>
              <p>Demo customer booking · check-in pending</p>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
