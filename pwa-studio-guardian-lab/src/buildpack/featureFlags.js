export const featureFlags = {
  ads: true,
  checkout: true,
  health: true,
  offlineEvents: true,
  rewards: true,
  tracking: true
};

export function isFeatureEnabled(key) {
  return featureFlags[key] === true;
}
