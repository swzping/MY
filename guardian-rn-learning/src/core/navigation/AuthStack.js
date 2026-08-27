import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';

import {modules} from '@app/config/modules';
import AuthLandingScreen from '@app/features/auth/AuthLandingScreen';

const Stack = createStackNavigator();

const AuthStack = () => (
  <Stack.Navigator screenOptions={{headerShown: false}}>
    <Stack.Screen name={modules.auth.name} component={AuthLandingScreen} />
  </Stack.Navigator>
);

export default AuthStack;
