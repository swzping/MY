import { createAdPool, getHomeAdConfig } from '../../lib/ads.js';

const adConfig = getHomeAdConfig('Hero');
const adPool = createAdPool([
  { id: 'ad-guardian-hero', title: 'Guardian weekend health sale' },
  { id: 'ad-skincare-class', title: 'Skin care class registration' }
]);
const consumedAds = [adPool.consume(), adPool.consume()];

export default function PageBuilderDemo({ onTrack }) {
  return (
    <section className="page-builder-demo">
      <div>
        <p className="eyebrow">PageBuilder + Ads</p>
        <h2>Campaign banner simulation</h2>
        <p>Lazy content, ad slot metadata, and click tracking in one teaching surface.</p>
        <div className="ad-debug-panel">
          <p><strong>slot:</strong> Hero</p>
          <p><strong>pageType:</strong> {adConfig.pageType}</p>
          <p><strong>adUnit:</strong> {adConfig.adUnit.join(', ')}</p>
          <ul>
            {consumedAds.map(ad => (
              <li key={ad.id}>{ad.id}: {ad.title}</li>
            ))}
          </ul>
        </div>
        <button onClick={() => onTrack('banner_click', 'home-hero-ad')}>Track banner click</button>
      </div>
    </section>
  );
}
