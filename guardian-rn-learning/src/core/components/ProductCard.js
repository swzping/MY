import React from 'react';
import {StyleSheet, TouchableOpacity, View} from 'react-native';
import {Text} from 'react-native-paper';

import ActionButton from '@app/components/ActionButton';
import {colors} from '@app/styles/theme';

const ProductCard = ({
  product,
  onPress,
  onAddToCart,
  actionLabel = 'View',
  compact = false,
}) => (
  <TouchableOpacity activeOpacity={0.9} onPress={onPress} style={[styles.card, compact && styles.compactCard]}>
    <View style={styles.imageBox}>
      <Text style={styles.imageInitial}>{product.name.charAt(0)}</Text>
      {product.badge ? <Text style={styles.badge}>{product.badge}</Text> : null}
    </View>
    <View style={styles.body}>
      <Text numberOfLines={2} style={styles.name}>{product.name}</Text>
      <Text numberOfLines={1} style={styles.meta}>{product.brand} / {product.category}</Text>
      <Text numberOfLines={2} style={styles.description}>{product.description}</Text>
      <View style={styles.ratingRow}>
        <Text style={styles.rating}>Rating {product.rating || '-'}</Text>
        <Text style={styles.stock}>{product.stockLabel}</Text>
      </View>
      <View style={styles.row}>
        <View>
          <Text style={styles.price}>${product.price.toFixed(2)}</Text>
          {product.originalPrice ? (
            <Text style={styles.originalPrice}>${product.originalPrice.toFixed(2)}</Text>
          ) : null}
        </View>
        {onAddToCart ? (
          <ActionButton onPress={onAddToCart}>Add</ActionButton>
        ) : (
          <ActionButton onPress={onPress}>{actionLabel}</ActionButton>
        )}
      </View>
    </View>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    flex: 1,
    overflow: 'hidden',
  },
  compactCard: {
    minHeight: 280,
  },
  imageBox: {
    alignItems: 'center',
    backgroundColor: '#F1F6EF',
    height: 118,
    justifyContent: 'center',
    position: 'relative',
  },
  imageInitial: {
    color: colors.primary,
    fontSize: 42,
    fontWeight: '900',
  },
  badge: {
    backgroundColor: colors.accent,
    borderRadius: 4,
    color: colors.surface,
    fontSize: 10,
    fontWeight: '800',
    left: 8,
    overflow: 'hidden',
    paddingHorizontal: 6,
    paddingVertical: 3,
    position: 'absolute',
    top: 8,
  },
  body: {
    gap: 6,
    padding: 10,
  },
  name: {color: colors.text, fontSize: 14, fontWeight: '800', minHeight: 36},
  meta: {color: colors.primaryDark, fontSize: 11, textTransform: 'uppercase'},
  description: {color: colors.muted, fontSize: 11, lineHeight: 16, minHeight: 32},
  ratingRow: {flexDirection: 'row', justifyContent: 'space-between'},
  rating: {color: colors.text, fontSize: 11, fontWeight: '700'},
  stock: {color: colors.muted, fontSize: 11},
  row: {alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', marginTop: 2},
  price: {color: colors.primary, fontSize: 16, fontWeight: '900'},
  originalPrice: {
    color: colors.muted,
    fontSize: 11,
    textDecorationLine: 'line-through',
  },
});

export default ProductCard;
