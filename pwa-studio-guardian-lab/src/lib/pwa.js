export function registerMockServiceWorker() {
  if (!('serviceWorker' in navigator)) {
    return Promise.resolve('service worker unavailable');
  }
  return navigator.serviceWorker
    .register('/mock-sw.js')
    .then(() => 'mock service worker registered')
    .catch(error => `mock service worker failed: ${error.message}`);
}
