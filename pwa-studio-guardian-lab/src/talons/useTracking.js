import { useCallback, useState } from 'react';
import { createTrackingEvent } from '../lib/tracking.js';

export function useTracking() {
  const [events, setEvents] = useState([]);

  const track = useCallback((type, label) => {
    setEvents(current => [...current, createTrackingEvent(type, label)]);
  }, []);

  return { events, track };
}
