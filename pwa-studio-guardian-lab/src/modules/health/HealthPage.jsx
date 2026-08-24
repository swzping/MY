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
      <article className="lab-card">
        <span>Health Result</span>
        <h3>Medical test result summary</h3>
        <p>Status: ready for customer review with apoteker follow-up available.</p>
      </article>
    </section>
  );
}
