import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';

import {modules, tabsApp} from '@app/config/modules';
import AppTabs from './AppTabs';
import ProductDetailScreen from '@app/features/product/ProductDetailScreen';
import CouponWalletScreen from '@app/features/coupons/CouponWalletScreen';
import CmsPageScreen from '@app/features/cms/CmsPageScreen';
import CampaignScreen from '@app/features/campaign/CampaignScreen';

const Stack = createStackNavigator();

const AppStack = () => (
  <Stack.Navigator screenOptions={{headerShown: false}}>
    <Stack.Screen name={tabsApp.name} component={AppTabs} />
    <Stack.Screen name={modules.productDetail.name} component={ProductDetailScreen} />
    <Stack.Screen name={modules.couponWallet.name} component={CouponWalletScreen} />
    <Stack.Screen name={modules.cms.name} component={CmsPageScreen} />
    <Stack.Screen name={modules.campaign.name} component={CampaignScreen} />
  </Stack.Navigator>
);

export default AppStack;
