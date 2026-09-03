import React from 'react';
import {StyleSheet, TouchableOpacity, View} from 'react-native';
import {Text} from 'react-native-paper';

import {colors} from '@app/styles/theme';

const Metric = ({label, value}) => (
  <View style={styles.metric}>
    <Text style={styles.metricValue}>{value}</Text>
    <Text style={styles.metricLabel}>{label}</Text>
  </View>
);

const LoyaltySummaryCard = ({summary, memberId, nextReward, onCouponsPress}) => (
  <View style={styles.card}>
    <View style={styles.headerRow}>
      <View style={styles.greetingWrap}>
        <Text style={styles.greeting} numberOfLines={1}>{summary.greeting}</Text>
        <Text style={styles.level} numberOfLines={1}>{summary.level}</Text>
      </View>
      <View style={styles.qrBox}>
        <Text style={styles.qrText}>QR</Text>
      </View>
    </View>
    <View style={styles.metrics}>
      <Metric label="Points" value={summary.pointsLabel} />
      <TouchableOpacity activeOpacity={0.8} onPress={onCouponsPress}>
        <Metric label="Coupons" value={summary.couponLabel} />
      </TouchableOpacity>
      <Metric label="Cart" value={summary.cartLabel} />
    </View>
    <View style={styles.footer}>
      <Text style={styles.memberId}>Member ID {memberId || 'Guest'}</Text>
      <Text style={styles.nextReward} numberOfLines={2}>{nextReward}</Text>
    </View>
  </View>
);

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.accent,
    borderBottomLeftRadius: 15,
    borderBottomRightRadius: 15,
    borderTopLeftRadius: 6,
    borderTopRightRadius: 6,
    overflow: 'hidden',
    padding: 16,
  },
  headerRow: {
    alignItems: 'flex-start',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  greetingWrap: {
    flex: 1,
    minWidth: 0,
    paddingRight: 12,
  },
  greeting: {
    color: colors.surface,
    fontSize: 18,
    fontWeight: '800',
  },
  level: {
    color: colors.surface,
    fontSize: 12,
    marginTop: 4,
    opacity: 0.9,
  },
  qrBox: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: 6,
    height: 52,
    justifyContent: 'center',
    width: 52,
  },
  qrText: {
    color: colors.primary,
    fontWeight: '900',
  },
  metrics: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 14,
    padding: 12,
  },
  metric: {
    minWidth: 78,
  },
  metricValue: {
    color: colors.text,
    fontSize: 15,
    fontWeight: '800',
  },
  metricLabel: {
    color: colors.muted,
    fontSize: 11,
    marginTop: 2,
  },
  footer: {
    backgroundColor: '#FFF8E8',
    borderRadius: 6,
    gap: 4,
    marginTop: 10,
    padding: 10,
  },
  memberId: {
    color: colors.primaryDark,
    fontSize: 11,
    fontWeight: '700',
  },
  nextReward: {
    color: colors.text,
    fontSize: 12,
  },
});

export default LoyaltySummaryCard;
