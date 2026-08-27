import React, {useEffect, useState} from 'react';
import {StyleSheet, View} from 'react-native';
import {Text} from 'react-native-paper';

import ActionButton from '@app/components/ActionButton';
import Screen from '@app/components/Screen';
import {Storage, storageKeys} from '@app/helpers/storage';
import {addCartItem} from '@app/helpers/cartLogic';
import {rxCartItems, showSnackbar, syncCartState} from '@app/services/cache';
import {mockGraphql} from '@app/services/mockGraphql';
import {colors} from '@app/styles/theme';

const ProductDetailScreen = ({navigation, route}) => {
  const [product, setProduct] = useState(null);
  const urlKey = route?.params?.productUrlKey;

  useEffect(() => {
    mockGraphql.getProductByUrlKey(urlKey).then(setProduct);
  }, [urlKey]);

  const addToCart = async () => {
    const nextItems = addCartItem(rxCartItems(), product);
    syncCartState(nextItems);
    await Storage.set(storageKeys.CART_ITEMS, nextItems);
    showSnackbar(`${product.name} added to cart`);
  };

  if (!product) {
    return <Screen title="Product">Loading product...</Screen>;
  }

  return (
    <Screen title={product.name} subtitle={product.description}>
      <View style={styles.hero}>
        <Text variant="headlineMedium">${product.price.toFixed(2)}</Text>
        <Text>SKU: {product.sku}</Text>
        <Text>Barcode: {product.barcode}</Text>
      </View>
      <ActionButton onPress={addToCart}>Add To Cart</ActionButton>
      <ActionButton mode="outlined" onPress={() => navigation.goBack()}>Back</ActionButton>
    </Screen>
  );
};

const styles = StyleSheet.create({
  hero: {backgroundColor: colors.surface, borderColor: colors.border, borderRadius: 8, borderWidth: 1, gap: 8, padding: 16},
});

export default ProductDetailScreen;
