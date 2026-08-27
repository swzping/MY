import React from 'react';
import {ScrollView, StyleSheet, View} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {Text} from 'react-native-paper';

import {colors} from '@app/styles/theme';

const Screen = ({title, subtitle, children, scroll = true}) => {
  const Wrapper = scroll ? ScrollView : View;

  return (
    <SafeAreaView style={styles.safe}>
      <Wrapper contentContainerStyle={scroll ? styles.content : null} style={!scroll ? styles.content : null}>
        {title ? <Text variant="headlineSmall" style={styles.title}>{title}</Text> : null}
        {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
        {children}
      </Wrapper>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safe: {flex: 1, backgroundColor: colors.page},
  content: {padding: 16, gap: 12},
  title: {fontWeight: '700', color: colors.text},
  subtitle: {color: colors.muted, lineHeight: 20},
});

export default Screen;
