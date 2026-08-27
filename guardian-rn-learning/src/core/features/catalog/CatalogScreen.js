import React, {useEffect, useState} from 'react';
import {SegmentedButtons} from 'react-native-paper';

import ProductCard from '@app/components/ProductCard';
import Screen from '@app/components/Screen';
import {navigateTo} from '@app/helpers/navigation';
import {mockGraphql} from '@app/services/mockGraphql';

const CatalogScreen = ({route}) => {
  const [filter, setFilter] = useState(route?.params?.value || 'all');
  const [products, setProducts] = useState([]);

  useEffect(() => {
    const filters = filter === 'all' ? {} : {category: filter};
    mockGraphql.getProducts(filters).then(result => setProducts(result.items));
  }, [filter]);

  return (
    <Screen title="Catalog" subtitle="A mock GraphQL product list with category filtering.">
      <SegmentedButtons
        value={filter}
        onValueChange={setFilter}
        buttons={[
          {value: 'all', label: 'All'},
          {value: 'vitamins', label: 'Vitamins'},
          {value: 'skincare', label: 'Skin'},
          {value: 'health', label: 'Health'},
        ]}
      />
      {products.map(product => (
        <ProductCard
          key={product.sku}
          product={product}
          onPress={() => navigateTo('productDetail', {productUrlKey: product.urlKey})}
        />
      ))}
    </Screen>
  );
};

export default CatalogScreen;
