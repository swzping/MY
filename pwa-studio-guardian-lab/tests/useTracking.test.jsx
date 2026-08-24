import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useTracking } from '../src/talons/useTracking.js';

describe('useTracking', () => {
  it('uses the shared tracking event shape', () => {
    vi.spyOn(Date, 'now').mockReturnValue(1710000000000);
    vi.spyOn(Math, 'random').mockReturnValue(0.5);
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-03-09T16:00:00.000Z'));

    const { result } = renderHook(() => useTracking());

    act(() => {
      result.current.track('click', 'hero');
    });

    expect(result.current.events).toEqual([
      {
        id: '1710000000000-8',
        type: 'click',
        label: 'hero',
        createdAt: '2024-03-09T16:00:00.000Z'
      }
    ]);

    vi.useRealTimers();
    vi.restoreAllMocks();
  });
});
