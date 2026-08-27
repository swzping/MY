import React from 'react';
import {Text} from 'react-native-paper';

import Screen from '@app/components/Screen';

const CmsPageScreen = ({route}) => (
  <Screen title="CMS Page" subtitle="Original deep links can open CMS pages or webview-backed content.">
    <Text>Identifier: {route?.params?.identifier || 'unknown'}</Text>
  </Screen>
);

export default CmsPageScreen;
