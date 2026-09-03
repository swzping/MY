import React from 'react';
import {StyleSheet, TextInput, TouchableOpacity, View} from 'react-native';
import {Badge, Text} from 'react-native-paper';
import {SafeAreaView} from 'react-native-safe-area-context';

import {colors} from '@app/styles/theme';

const IconButton = ({label, badge, onPress}) => (
  <TouchableOpacity activeOpacity={0.8} onPress={onPress} style={styles.iconButton}>
    <Text style={styles.iconLabel}>{label}</Text>
    {badge ? <Badge size={16} style={styles.badge}>{badge}</Badge> : null}
  </TouchableOpacity>
);

const LearningToolbar = ({
  searchValue = '',
  onSearchChange,
  onSearchSubmit,
  onWishlistPress,
  onNotificationPress,
  notificationCount = 0,
  cartQty = 0,
}) => (
  <SafeAreaView edges={['top']} style={styles.safeArea}>
    <View style={styles.header}>
      <View style={styles.logoWrap}>
        <Text style={styles.logo}>G</Text>
      </View>
      <View style={styles.searchWrap}>
        <Text style={styles.searchIcon}>S</Text>
        <TextInput
          value={searchValue}
          onChangeText={onSearchChange}
          onSubmitEditing={onSearchSubmit}
          placeholder="Search Guardian products"
          placeholderTextColor="rgba(255,255,255,0.78)"
          returnKeyType="search"
          style={styles.searchInput}
        />
      </View>
      <View style={styles.actions}>
        <IconButton label="W" onPress={onWishlistPress} />
        <IconButton label="N" badge={notificationCount > 0 ? notificationCount : null} onPress={onNotificationPress} />
        <IconButton label="C" badge={cartQty > 0 ? cartQty : null} />
      </View>
    </View>
  </SafeAreaView>
);

const styles = StyleSheet.create({
  safeArea: {
    backgroundColor: colors.primary,
  },
  header: {
    alignItems: 'center',
    backgroundColor: colors.primary,
    flexDirection: 'row',
    gap: 10,
    minHeight: 58,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  logoWrap: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: 18,
    height: 36,
    justifyContent: 'center',
    width: 36,
  },
  logo: {
    color: colors.primary,
    fontSize: 23,
    fontWeight: '900',
    lineHeight: 28,
  },
  searchWrap: {
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.18)',
    borderColor: 'rgba(255,255,255,0.34)',
    borderRadius: 18,
    borderWidth: 1,
    flex: 1,
    flexDirection: 'row',
    height: 38,
    paddingHorizontal: 10,
  },
  searchIcon: {
    color: colors.surface,
    fontSize: 18,
    marginRight: 6,
  },
  searchInput: {
    color: colors.surface,
    flex: 1,
    fontSize: 13,
    height: 38,
    padding: 0,
  },
  actions: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 6,
  },
  iconButton: {
    alignItems: 'center',
    height: 34,
    justifyContent: 'center',
    position: 'relative',
    width: 28,
  },
  iconLabel: {
    color: colors.surface,
    fontSize: 18,
    fontWeight: '700',
  },
  badge: {
    backgroundColor: colors.danger,
    position: 'absolute',
    right: -2,
    top: -2,
  },
});

export default LearningToolbar;
