import React from 'react';
import {useReactiveVar} from '@apollo/client';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';

import {modules} from '@app/config/modules';
import {rxCartQty} from '@app/services/cache';
import HomeScreen from '@app/features/home/HomeScreen';
import CatalogScreen from '@app/features/catalog/CatalogScreen';
import CartScreen from '@app/features/cart/CartScreen';
import ScannerScreen from '@app/features/scanner/ScannerScreen';
import AccountScreen from '@app/features/account/AccountScreen';

const Tab = createBottomTabNavigator();

const AppTabs = () => {
  const cartQty = useReactiveVar(rxCartQty);

  return (
    <Tab.Navigator screenOptions={{headerShown: false}}>
      <Tab.Screen name={modules.home.name} component={HomeScreen} options={{tabBarLabel: modules.home.label}} />
      <Tab.Screen name={modules.catalog.name} component={CatalogScreen} options={{tabBarLabel: modules.catalog.label}} />
      <Tab.Screen name={modules.cart.name} component={CartScreen} options={{tabBarLabel: `${modules.cart.label} (${cartQty})`}} />
      <Tab.Screen name={modules.scanner.name} component={ScannerScreen} options={{tabBarLabel: modules.scanner.label}} />
      <Tab.Screen name={modules.account.name} component={AccountScreen} options={{tabBarLabel: modules.account.label}} />
    </Tab.Navigator>
  );
};

export default AppTabs;
