import { useEffect, useState } from 'react';
import { operations } from '../../graphql/operations.js';

export default function CatalogPage({ cart, executeGraphQL, onTrack }) {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    let mounted = true;

    executeGraphQL(operations.getProducts).then(result => {
      if (mounted && result.ok) setProducts(result.data.products);
    });

    return () => {
      mounted = false;
    };
  }, [executeGraphQL]);

  return (
    <section className="page-grid">
      <div>
        <p className="eyebrow">Catalog</p>
        <h2>Mock Magento Product Grid</h2>
        <p>Products come from the local mock GraphQL client after the auth refresh talon runs.</p>
      </div>
      <div className="cards-grid">
        {products.map(product => (
          <article className="lab-card" key={product.id}>
            <span>{product.category}</span>
            <h3>{product.name}</h3>
            <p>IDR {product.price.toLocaleString('id-ID')}</p>
            <p>SKU {product.id} · local GraphQL product card</p>
            <div className="button-row inline-actions">
              <button onClick={() => cart.addItem(product)}>Add to cart</button>
              <button onClick={() => onTrack('product_click', product.id)}>Track click</button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
