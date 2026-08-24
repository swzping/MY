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

export default function CheckoutPage({ cart }) {
  return (
    <section className="page-grid">
      <div>
        <p className="eyebrow">Checkout</p>
        <h2>Payment registry demo</h2>
        <p>Payment methods are registered by code, like PWA Studio checkout payment targets.</p>
      </div>
      <article className="lab-card cart-overview">
        <span>Cart Overview</span>
        <h3>{cart.items.length} item{cart.items.length === 1 ? '' : 's'}</h3>
        <p>Total IDR {cart.total.toLocaleString('id-ID')}</p>
        <ul>
          {cart.items.map((item, index) => (
            <li key={`${item.id}-${index}`}>
              {item.name} x {item.quantity}
            </li>
          ))}
        </ul>
      </article>
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
