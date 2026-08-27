import React from 'react';
import {useReactiveVar} from '@apollo/client';
import {NavigationContainer} from '@react-navigation/native';
import {ActivityIndicator} from 'react-native-paper';
import {View} from 'react-native';

import SnackbarHost from '@app/components/SnackbarHost';
import {modules} from '@app/config/modules';
import {navigationRef} from '@app/helpers/navigation';
import {rxAppLoading, rxAppMaintenance, rxUserToken} from '@app/services/cache';
import AppStack from './AppStack';
import AuthStack from './AuthStack';
import MaintenanceScreen from '@app/features/maintenance/MaintenanceScreen';

const AppNavigator = () => {
  const loading = useReactiveVar(rxAppLoading);
  const maintenance = useReactiveVar(rxAppMaintenance);
  const token = useReactiveVar(rxUserToken);

  if (loading) {
    return (
      <View style={{alignItems: 'center', flex: 1, justifyContent: 'center'}}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <>
      <NavigationContainer ref={navigationRef}>
        {maintenance ? <MaintenanceScreen /> : token ? <AppStack /> : <AuthStack initialRouteName={modules.auth.name} />}
      </NavigationContainer>
      <SnackbarHost />
    </>
  );
};

export default AppNavigator;
