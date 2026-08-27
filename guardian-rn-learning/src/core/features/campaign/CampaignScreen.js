import React from 'react';
import {Text} from 'react-native-paper';

import Screen from '@app/components/Screen';

const CampaignScreen = ({route}) => (
  <Screen title="Campaign" subtitle="A placeholder route for activity, gamification, or marketing deep links.">
    <Text>Campaign: {route?.params?.campaign || 'guardian-run'}</Text>
  </Screen>
);

export default CampaignScreen;
