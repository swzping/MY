import React from 'react';
import {useReactiveVar} from '@apollo/client';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {Pressable, StyleSheet, Text} from 'react-native';

import TabBarIcon from '@app/components/TabBarIcon';
import {modules} from '@app/config/modules';
import {rxCartQty} from '@app/services/cache';
import {colors} from '@app/styles/theme';
import HomeScreen from '@app/features/home/HomeScreen';
import CatalogScreen from '@app/features/catalog/CatalogScreen';
import CartScreen from '@app/features/cart/CartScreen';
import ScannerScreen from '@app/features/scanner/ScannerScreen';
import AccountScreen from '@app/features/account/AccountScreen';

const Tab = createBottomTabNavigator();

const inactiveColor = '#5F665F';

const TabButton = props => (
  <Pressable {...props} android_ripple={{color: 'transparent'}} style={props.style} />
);

const renderLabel = label => ({focused}) => (
  <Text
    adjustsFontSizeToFit
    numberOfLines={1}
    style={[styles.label, focused ? styles.activeLabel : styles.inactiveLabel]}>
    {label}
  </Text>
);

const tabOptions = (label, iconName, badge) => ({
  lazy: true,
  tabBarAccessibilityLabel: label,
  tabBarIcon: ({focused}) => (
    <TabBarIcon badge={badge} focused={focused} name={iconName} />
  ),
  tabBarLabel: renderLabel(label),
});

const AppTabs = () => {
  const cartQty = useReactiveVar(rxCartQty);

  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarButton: TabButton,
        tabBarHideOnKeyboard: true,
        tabBarIconStyle: styles.iconSlot,
        tabBarInactiveTintColor: inactiveColor,
        tabBarItemStyle: styles.item,
        tabBarLabelPosition: 'below-icon',
        tabBarStyle: styles.bar,
      }}>
      <Tab.Screen
        component={HomeScreen}
        name={modules.home.name}
        options={tabOptions(modules.home.label, 'home')}
      />
      <Tab.Screen
        component={CatalogScreen}
        name={modules.catalog.name}
        options={tabOptions(modules.catalog.label, 'catalog')}
      />
      <Tab.Screen
        component={CartScreen}
        name={modules.cart.name}
        options={tabOptions(modules.cart.label, 'cart', cartQty)}
      />
      <Tab.Screen
        component={ScannerScreen}
        name={modules.scanner.name}
        options={tabOptions(modules.scanner.label, 'scanner')}
      />
      <Tab.Screen
        component={AccountScreen}
        name={modules.account.name}
        options={tabOptions(modules.account.label, 'account')}
      />
    </Tab.Navigator>
  );
};

const styles = StyleSheet.create({
  bar: {
    backgroundColor: colors.surface,
    borderTopColor: '#E4E9E2',
    borderTopWidth: 1,
    elevation: 10,
    height: 78,
    paddingBottom: 18,
    paddingTop: 7,
    shadowColor: '#000000',
    shadowOffset: {width: 0, height: -3},
    shadowOpacity: 0.08,
    shadowRadius: 8,
  },
  item: {
    paddingVertical: 2,
  },
  iconSlot: {
    marginTop: 2,
  },
  label: {
    fontSize: 10,
    fontWeight: '600',
    lineHeight: 12,
    maxWidth: 76,
    textAlign: 'center',
  },
  activeLabel: {
    color: colors.primary,
  },
  inactiveLabel: {
    color: inactiveColor,
  },
});

export default AppTabs;
