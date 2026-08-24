import { mockData } from '../../graphql/mockData.js';

const freeGifts = [
  { id: 'gift-1', name: 'Mini vitamin sample', trigger: 'Cart over IDR 150,000' },
  { id: 'gift-2', name: 'Skin care pouch', trigger: 'Coupon GIFTREADY' }
];

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
      <section>
        <p className="eyebrow">Free Gift</p>
        <div className="cards-grid">
          {freeGifts.map(gift => (
            <article className="lab-card" key={gift.id}>
              <span>{gift.trigger}</span>
              <h3>{gift.name}</h3>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
