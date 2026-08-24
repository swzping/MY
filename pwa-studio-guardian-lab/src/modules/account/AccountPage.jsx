import { useEffect, useState } from 'react';
import { operations } from '../../graphql/operations.js';

export default function AccountPage({ executeGraphQL }) {
  const [dashboard, setDashboard] = useState(null);

  useEffect(() => {
    let mounted = true;

    executeGraphQL(operations.getCustomerDashboard).then(result => {
      if (mounted && result.ok) setDashboard(result.data);
    });

    return () => {
      mounted = false;
    };
  }, [executeGraphQL]);

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
