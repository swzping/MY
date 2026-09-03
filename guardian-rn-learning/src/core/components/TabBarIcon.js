import React from 'react';
import {StyleSheet, Text, View} from 'react-native';

import {colors} from '@app/styles/theme';

const inactiveColor = '#5F665F';
const activeColor = '#B77905';

const HomeMark = ({color}) => (
  <View style={styles.homeWrap}>
    <View style={[styles.homeRoof, {borderColor: color}]} />
    <View style={[styles.homeBody, {borderColor: color}]}>
      <View style={[styles.homeDoor, {backgroundColor: color}]} />
    </View>
  </View>
);

const CategoryMark = ({color}) => (
  <View style={styles.gridWrap}>
    {[0, 1, 2, 3].map(item => (
      <View key={item} style={[styles.gridCell, {borderColor: color}]} />
    ))}
  </View>
);

const CartMark = ({color}) => (
  <View style={styles.cartWrap}>
    <View style={[styles.cartHandle, {backgroundColor: color}]} />
    <View style={[styles.cartBasket, {borderColor: color}]} />
    <View style={styles.cartWheels}>
      <View style={[styles.cartWheel, {backgroundColor: color}]} />
      <View style={[styles.cartWheel, {backgroundColor: color}]} />
    </View>
  </View>
);

const ScanMark = ({color}) => (
  <View style={styles.scanWrap}>
    <View style={[styles.scanCorner, styles.scanTopLeft, {borderColor: color}]} />
    <View style={[styles.scanCorner, styles.scanTopRight, {borderColor: color}]} />
    <View style={[styles.scanCorner, styles.scanBottomLeft, {borderColor: color}]} />
    <View style={[styles.scanCorner, styles.scanBottomRight, {borderColor: color}]} />
    <View style={[styles.scanLine, {backgroundColor: color}]} />
  </View>
);

const AccountMark = ({color}) => (
  <View style={styles.accountWrap}>
    <View style={[styles.accountHead, {borderColor: color}]} />
    <View style={[styles.accountBody, {borderColor: color}]} />
  </View>
);

const marks = {
  home: HomeMark,
  catalog: CategoryMark,
  cart: CartMark,
  scanner: ScanMark,
  account: AccountMark,
};

const TabBarIcon = ({name, focused, badge}) => {
  const color = focused ? activeColor : inactiveColor;
  const Mark = marks[name] || HomeMark;
  const normalizedBadge = Number(badge || 0);

  return (
    <View style={[styles.container, focused && styles.activeContainer]}>
      <Mark color={color} />
      {normalizedBadge > 0 ? (
        <View style={styles.badge}>
          <Text adjustsFontSizeToFit numberOfLines={1} style={styles.badgeText}>
            {normalizedBadge > 99 ? '99+' : normalizedBadge}
          </Text>
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    borderRadius: 16,
    height: 31,
    justifyContent: 'center',
    position: 'relative',
    width: 42,
  },
  activeContainer: {
    backgroundColor: '#FFF1CC',
  },
  badge: {
    alignItems: 'center',
    backgroundColor: colors.danger,
    borderColor: colors.surface,
    borderRadius: 10,
    borderWidth: 1,
    height: 19,
    justifyContent: 'center',
    minWidth: 19,
    paddingHorizontal: 4,
    position: 'absolute',
    right: 1,
    top: -3,
  },
  badgeText: {
    color: colors.surface,
    fontSize: 9,
    fontWeight: '800',
    lineHeight: 11,
  },
  homeWrap: {
    height: 24,
    position: 'relative',
    width: 24,
  },
  homeRoof: {
    borderLeftWidth: 2,
    borderTopWidth: 2,
    height: 15,
    left: 5,
    position: 'absolute',
    top: 2,
    transform: [{rotate: '45deg'}],
    width: 15,
  },
  homeBody: {
    alignItems: 'center',
    borderBottomWidth: 2,
    borderLeftWidth: 2,
    borderRightWidth: 2,
    bottom: 2,
    height: 12,
    justifyContent: 'flex-end',
    left: 4,
    position: 'absolute',
    width: 16,
  },
  homeDoor: {
    height: 6,
    width: 4,
  },
  gridWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 3,
    height: 21,
    width: 21,
  },
  gridCell: {
    borderRadius: 3,
    borderWidth: 2,
    height: 9,
    width: 9,
  },
  cartWrap: {
    height: 23,
    justifyContent: 'center',
    width: 24,
  },
  cartHandle: {
    borderRadius: 1,
    height: 2,
    marginBottom: 2,
    marginLeft: 1,
    transform: [{rotate: '-12deg'}],
    width: 8,
  },
  cartBasket: {
    borderBottomWidth: 2,
    borderLeftWidth: 2,
    borderRadius: 3,
    borderRightWidth: 2,
    borderTopWidth: 2,
    height: 10,
    marginLeft: 5,
    width: 16,
  },
  cartWheels: {
    flexDirection: 'row',
    gap: 8,
    marginLeft: 8,
    marginTop: 2,
  },
  cartWheel: {
    borderRadius: 2,
    height: 4,
    width: 4,
  },
  scanWrap: {
    height: 24,
    position: 'relative',
    width: 24,
  },
  scanCorner: {
    height: 8,
    position: 'absolute',
    width: 8,
  },
  scanTopLeft: {
    borderLeftWidth: 2,
    borderTopWidth: 2,
    left: 2,
    top: 2,
  },
  scanTopRight: {
    borderRightWidth: 2,
    borderTopWidth: 2,
    right: 2,
    top: 2,
  },
  scanBottomLeft: {
    borderBottomWidth: 2,
    borderLeftWidth: 2,
    bottom: 2,
    left: 2,
  },
  scanBottomRight: {
    borderBottomWidth: 2,
    borderRightWidth: 2,
    bottom: 2,
    right: 2,
  },
  scanLine: {
    borderRadius: 1,
    height: 2,
    left: 6,
    position: 'absolute',
    top: 11,
    width: 12,
  },
  accountWrap: {
    alignItems: 'center',
    height: 24,
    justifyContent: 'center',
    width: 24,
  },
  accountHead: {
    borderRadius: 6,
    borderWidth: 2,
    height: 10,
    marginBottom: 2,
    width: 10,
  },
  accountBody: {
    borderRadius: 8,
    borderTopWidth: 2,
    height: 9,
    width: 18,
  },
});

export default TabBarIcon;
