export function createTrackingEvent(type, label) {
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    type,
    label,
    createdAt: new Date().toISOString()
  };
}
