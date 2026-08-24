export const OSMOS_H5_MAX_WIDTH = 767;

const getViewportWidth = () =>
  typeof window === 'undefined' ? OSMOS_H5_MAX_WIDTH + 1 : window.innerWidth;

export function isH5(width = getViewportWidth()) {
  return width <= OSMOS_H5_MAX_WIDTH;
}

export function getHomeAdConfig(slot, width = getViewportWidth()) {
  const prefix = isH5(width) ? 'GUIDMWeb' : 'GUIDDWeb';
  return {
    pageType: `${prefix}HomePage`,
    adUnit: [`${prefix}${slot}`]
  };
}

export function createAdPool(ads) {
  let index = 0;
  return {
    consume() {
      const ad = ads[index] || null;
      index += 1;
      return ad;
    },
    reset() {
      index = 0;
    }
  };
}
