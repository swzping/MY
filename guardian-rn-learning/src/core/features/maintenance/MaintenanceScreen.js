import React from 'react';
import {Text} from 'react-native-paper';

import ActionButton from '@app/components/ActionButton';
import Screen from '@app/components/Screen';
import {rxAppMaintenance, showSnackbar} from '@app/services/cache';

const MaintenanceScreen = () => (
  <Screen title="Maintenance Mode" subtitle="The source app can gate the whole navigator from Firestore and Remote Config.">
    <Text>This full-screen state demonstrates the same navigation gate with local reactive state.</Text>
    <ActionButton onPress={() => {
      rxAppMaintenance(false);
      showSnackbar('Maintenance mode disabled');
    }}>
      Leave Maintenance
    </ActionButton>
  </Screen>
);

export default MaintenanceScreen;
