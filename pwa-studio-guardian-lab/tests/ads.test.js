// @vitest-environment node

import { describe, expect, it } from 'vitest';
import { getHomeAdConfig, isH5, OSMOS_H5_MAX_WIDTH } from '../src/lib/ads.js';

describe('ads helpers', () => {
  it('uses a desktop fallback outside browser contexts', () => {
    expect(isH5()).toBe(false);
    expect(getHomeAdConfig('Top')).toEqual({
      pageType: 'GUIDDWebHomePage',
      adUnit: ['GUIDDWebTop']
    });
  });

  it('classifies explicit h5 widths', () => {
    expect(isH5(OSMOS_H5_MAX_WIDTH)).toBe(true);
    expect(getHomeAdConfig('Hero', 390)).toEqual({
      pageType: 'GUIDMWebHomePage',
      adUnit: ['GUIDMWebHero']
    });
  });
});
