import React from 'react';
import {Text} from 'react-native-paper';

import Screen from '@app/components/Screen';

const HomeScreen = () => (
  <Screen title="Core Home" subtitle="This file is the base home screen from src/core." >
    <Text>The override layer can replace this screen without changing navigation imports.</Text>
  </Screen>
);

export default HomeScreen;
