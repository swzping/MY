import React, {useEffect, useState} from 'react';
import {StyleSheet, TouchableOpacity, View} from 'react-native';
import {useReactiveVar} from '@apollo/client';
import {SegmentedButtons, Text} from 'react-native-paper';

import LearningToolbar from '@app/components/LearningToolbar';
import ProductCard from '@app/components/ProductCard';
import Screen from '@app/components/Screen';
import {addCartItem} from '@app/helpers/cartLogic';
import {buildProductListSummary} from '@app/helpers/homeViewModel';
import {navigateTo} from '@app/helpers/navigation';
import {rxCartItems, rxCartQty, showSnackbar, syncCartState} from '@app/services/cache';
import {mockGraphql} from '@app/services/mockGraphql';
import {colors} from '@app/styles/theme';

const Pill = ({children, active, onPress}) => (
  <TouchableOpacity activeOpacity={0.82} onPress={onPress} style={[styles.pill, active && styles.pillActive]}>
    <Text style={[styles.pillText, active && styles.pillTextActive]}>{children}</Text>
  </TouchableOpacity>
);

const CatalogScreen = ({route}) => {
  const [filter, setFilter] = useState(route?.params?.value || 'all');
  const [products, setProducts] = useState([]);
  const [sort, setSort] = useState('featured');
  const cartQty = useReactiveVar(rxCartQty);

  useEffect(() => {
    const filters = filter === 'all' ? {} : {category: filter};
    mockGraphql.getProducts(filters).then(result => {
      const items = [...result.items].sort((a, b) => {
        if (sort === 'price-low') {
          return a.price - b.price;
        }
        if (sort === 'rating') {
          return b.rating - a.rating;
        }
        return a.sku.localeCompare(b.sku);
      });
      setProducts(items);
    });
  }, [filter, sort]);

  const summary = buildProductListSummary(products, filter);

  const addProduct = product => {
    const nextItems = addCartItem(rxCartItems(), product);
    syncCartState(nextItems);
    showSnackbar(`${product.name} added to cart`);
  };

  return (
    <View style={styles.root}>
      <LearningToolbar
        cartQty={cartQty}
        notificationCount={3}
        onNotificationPress={() => showSnackbar('Notifications are mocked')}
        onWishlistPress={() => showSnackbar('Wishlist is mocked')}
      />
      <Screen scroll>
        <View style={styles.banner}>
          <Text style={styles.bannerTitle}>Health essentials</Text>
          <Text style={styles.bannerCopy}>A learning PLP inspired by Guardian's product listing flow.</Text>
        </View>

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

        <View style={styles.listHeader}>
          <View>
            <Text style={styles.resultText}>{summary.totalLabel}</Text>
            <Text style={styles.summaryText}>{summary.filterLabel} / {summary.brandCountLabel}</Text>
          </View>
          <View style={styles.pillRow}>
            <Pill active={sort === 'featured'} onPress={() => setSort('featured')}>Sort</Pill>
            <Pill active={sort === 'price-low'} onPress={() => setSort('price-low')}>Price</Pill>
            <Pill active={sort === 'rating'} onPress={() => setSort('rating')}>Rating</Pill>
            <Pill onPress={() => showSnackbar('Filter sheet is mocked in this lab')}>Filter</Pill>
          </View>
        </View>

        <View style={styles.grid}>
          {products.map(product => (
            <View key={product.sku} style={styles.gridItem}>
              <ProductCard
                compact
                product={product}
                onAddToCart={() => addProduct(product)}
                onPress={() => navigateTo('productDetail', {productUrlKey: product.urlKey})}
              />
            </View>
          ))}
        </View>
      </Screen>
    </View>
  );
};

const styles = StyleSheet.create({
  root: {
    backgroundColor: colors.page,
    flex: 1,
  },
  banner: {
    backgroundColor: colors.primaryDark,
    borderRadius: 8,
    padding: 16,
  },
  bannerTitle: {
    color: colors.surface,
    fontSize: 20,
    fontWeight: '900',
  },
  bannerCopy: {
    color: colors.surface,
    fontSize: 12,
    marginTop: 4,
    opacity: 0.88,
  },
  listHeader: {
    alignItems: 'flex-start',
    backgroundColor: colors.surface,
    borderRadius: 8,
    gap: 10,
    padding: 12,
  },
  resultText: {
    color: colors.text,
    fontSize: 13,
    fontWeight: '800',
  },
  summaryText: {
    color: colors.muted,
    fontSize: 11,
    marginTop: 2,
  },
  pillRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  pill: {
    backgroundColor: '#F5F5F0',
    borderColor: colors.border,
    borderRadius: 18,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  pillActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  pillText: {
    color: colors.text,
    fontSize: 12,
    fontWeight: '700',
  },
  pillTextActive: {
    color: colors.surface,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  gridItem: {
    width: '48.5%',
  },
});

export default CatalogScreen;
