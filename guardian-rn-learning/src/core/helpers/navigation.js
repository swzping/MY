import {createNavigationContainerRef} from '@react-navigation/native';

import {modules} from '@app/config/modules';
import {showSnackbar} from '@app/services/cache';

export const navigationRef = createNavigationContainerRef();

export const navigateTo = (moduleKey, params = {}) => {
  const module = modules[moduleKey];

  if (!module?.enable) {
    showSnackbar(`${module?.label || moduleKey} module is disabled`);
    return;
  }

  if (navigationRef.isReady()) {
    navigationRef.navigate(module.name, params);
  }
};

export const routeFromResolvedLink = resolved => {
  if (!resolved) {
    return null;
  }

  if (resolved.type === 'product') {
    return {route: modules.productDetail.name, params: {productUrlKey: resolved.value}};
  }

  if (resolved.type === 'category' || resolved.type === 'brand') {
    return {route: modules.catalog.name, params: {type: resolved.type, value: resolved.value}};
  }

  if (resolved.type === 'cms') {
    return {route: modules.cms.name, params: {identifier: resolved.value}};
  }

  if (resolved.type === 'campaign') {
    return {route: modules.campaign.name, params: {campaign: resolved.value}};
  }

  return null;
};
