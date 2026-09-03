import React from 'react';
import {StyleSheet, TouchableOpacity, View} from 'react-native';
import {useReactiveVar} from '@apollo/client';
import {Text} from 'react-native-paper';

import ActionButton from '@app/components/ActionButton';
import LearningToolbar from '@app/components/LearningToolbar';
import LoyaltySummaryCard from '@app/components/LoyaltySummaryCard';
import ProductCard from '@app/components/ProductCard';
import Screen from '@app/components/Screen';
import {modules} from '@app/config/modules';
import {member, products} from '@app/data/mockData';
import {addCartItem} from '@app/helpers/cartLogic';
import {buildMemberSummary} from '@app/helpers/homeViewModel';
import {navigateTo} from '@app/helpers/navigation';
import {
  rxCartItems,
  rxCartQty,
  rxSelectedCoupon,
  rxUserInformation,
  rxUserRewardPoint,
  rxUserType,
  showSnackbar,
  syncCartState,
} from '@app/services/cache';
import {colors} from '@app/styles/theme';

const Shortcut = ({label, value, onPress}) => (
  <TouchableOpacity activeOpacity={0.82} onPress={onPress} style={styles.shortcut}>
    <Text style={styles.shortcutValue}>{value}</Text>
    <Text style={styles.shortcutLabel}>{label}</Text>
  </TouchableOpacity>
);

const HomeScreen = () => {
  const user = useReactiveVar(rxUserInformation);
  const userType = useReactiveVar(rxUserType);
  const points = useReactiveVar(rxUserRewardPoint);
  const cartQty = useReactiveVar(rxCartQty);
  const selectedCoupon = useReactiveVar(rxSelectedCoupon);
  const summary = buildMemberSummary({
    user: user || member,
    userType,
    points,
    couponCount: selectedCoupon ? 1 : 2,
    cartQty,
  });

  const addFeaturedProduct = product => {
    const nextItems = addCartItem(rxCartItems(), product);
    syncCartState(nextItems);
    showSnackbar(`${product.name} added to cart`);
  };

  return (
    <View style={styles.root}>
      <LearningToolbar
        cartQty={cartQty}
        notificationCount={3}
        onNotificationPress={() => showSnackbar('3 unread notifications')}
        onSearchSubmit={() => navigateTo('catalog')}
        onWishlistPress={() => showSnackbar('Wishlist is mocked in this lab')}
      />
      <Screen scroll>
        <LoyaltySummaryCard
          summary={summary}
          memberId={member.memberId}
          nextReward={member.nextReward}
          onCouponsPress={() => navigateTo('couponWallet')}
        />

        <View style={styles.shortcuts}>
          <Shortcut label="Modules" value={Object.keys(modules).length} onPress={() => showSnackbar('Module registry lives in src/core/config/modules.js')} />
          <Shortcut label="Points" value={summary.pointsLabel} onPress={() => showSnackbar('Points are held in Apollo reactive variables')} />
          <Shortcut label="Coupons" value={summary.couponLabel} onPress={() => navigateTo('couponWallet')} />
        </View>

        <View style={styles.promo}>
          <View>
            <Text style={styles.promoTitle}>Member Weekend</Text>
            <Text style={styles.promoCopy}>Save more on vitamins, skincare, and wellness picks.</Text>
          </View>
          <ActionButton mode="contained" onPress={() => navigateTo('catalog')}>Shop</ActionButton>
        </View>

        <View style={styles.sectionHeader}>
          <View>
            <Text variant="titleMedium" style={styles.heading}>Featured for you</Text>
            <Text style={styles.subheading}>Mock GraphQL products rendered like a PLP tile.</Text>
          </View>
          <ActionButton mode="text" onPress={() => navigateTo('catalog')}>View All</ActionButton>
        </View>

        <View style={styles.grid}>
          {products.slice(0, 4).map(product => (
            <View key={product.sku} style={styles.gridItem}>
              <ProductCard
                compact
                product={product}
                onAddToCart={() => addFeaturedProduct(product)}
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
  shortcuts: {
    flexDirection: 'row',
    gap: 8,
  },
  shortcut: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    flex: 1,
    padding: 12,
  },
  shortcutValue: {
    color: colors.primary,
    fontSize: 16,
    fontWeight: '900',
  },
  shortcutLabel: {
    color: colors.muted,
    fontSize: 11,
    marginTop: 4,
  },
  promo: {
    alignItems: 'center',
    backgroundColor: colors.primaryDark,
    borderRadius: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 14,
  },
  promoTitle: {
    color: colors.surface,
    fontSize: 17,
    fontWeight: '900',
  },
  promoCopy: {
    color: colors.surface,
    fontSize: 12,
    marginTop: 4,
    maxWidth: 210,
    opacity: 0.88,
  },
  sectionHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  heading: {color: colors.text, fontWeight: '800'},
  subheading: {color: colors.muted, fontSize: 12, marginTop: 2},
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  gridItem: {
    width: '48.5%',
  },
});

export default HomeScreen;
