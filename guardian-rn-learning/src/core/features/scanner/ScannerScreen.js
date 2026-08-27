import React, {useState} from 'react';
import {StyleSheet, View} from 'react-native';
import {Text, TextInput} from 'react-native-paper';

import ActionButton from '@app/components/ActionButton';
import Screen from '@app/components/Screen';
import {linkExamples} from '@app/data/mockData';
import {routeFromResolvedLink} from '@app/helpers/navigation';
import {parseGuardianLink, resolveScannerInput} from '@app/helpers/deepLink';
import {showSnackbar} from '@app/services/cache';
import {colors} from '@app/styles/theme';

const ScannerScreen = ({navigation}) => {
  const [scanValue, setScanValue] = useState('8991002100012');

  const runScan = () => {
    const result = resolveScannerInput(scanValue);

    if (!result.route) {
      showSnackbar(result.message);
      return;
    }

    navigation.navigate(result.route, result.params);
  };

  const runDeepLink = example => {
    const route = routeFromResolvedLink(parseGuardianLink(example));

    if (!route) {
      showSnackbar('Link could not be routed');
      return;
    }

    navigation.navigate(route.route, route.params);
  };

  return (
    <Screen title="Scanner Simulator" subtitle="The source app uses Vision Camera. This learning version uses typed barcode and QR examples so the routing logic stays easy to test.">
      <TextInput label="Barcode or Guardian URL" value={scanValue} onChangeText={setScanValue} mode="outlined" />
      <ActionButton onPress={runScan}>Resolve Scan</ActionButton>
      <View style={styles.examples}>
        <Text variant="titleMedium">Deep link examples</Text>
        {linkExamples.map(example => (
          <ActionButton key={example} mode="outlined" onPress={() => runDeepLink(example)}>
            {example.replace('https://guardian.test/', '')}
          </ActionButton>
        ))}
      </View>
    </Screen>
  );
};

const styles = StyleSheet.create({
  examples: {backgroundColor: colors.surface, borderColor: colors.border, borderRadius: 8, borderWidth: 1, gap: 8, padding: 14},
});

export default ScannerScreen;
