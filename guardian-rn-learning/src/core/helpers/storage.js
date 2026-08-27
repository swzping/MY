import AsyncStorage from '@react-native-async-storage/async-storage';

export const storageKeys = {
  TOKEN: 'GUARDIAN_LEARNING_TOKEN',
  USER_TYPE: 'GUARDIAN_LEARNING_USER_TYPE',
  CART_ITEMS: 'GUARDIAN_LEARNING_CART_ITEMS',
  SELECTED_COUPON: 'GUARDIAN_LEARNING_SELECTED_COUPON',
};

export const Storage = {
  set: async (name, data) => {
    await AsyncStorage.setItem(name, JSON.stringify(data));
  },
  get: async name => {
    const value = await AsyncStorage.getItem(name);
    return value ? JSON.parse(value) : null;
  },
  del: async name => {
    await AsyncStorage.removeItem(name);
  },
  clearLearningState: async () => {
    await Promise.all(Object.values(storageKeys).map(key => AsyncStorage.removeItem(key)));
  },
};
