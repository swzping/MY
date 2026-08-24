export type NotificationTargetTab = "home" | "record" | "budget" | "analysis";

const targetTabs: readonly NotificationTargetTab[] = ["home", "record", "budget", "analysis"];

export function getNotificationTargetTab(data: unknown): NotificationTargetTab | null {
  if (!data || typeof data !== "object" || !("targetTab" in data)) {
    return null;
  }

  const targetTab = (data as { targetTab?: unknown }).targetTab;
  if (typeof targetTab !== "string") {
    return null;
  }

  return targetTabs.includes(targetTab as NotificationTargetTab)
    ? (targetTab as NotificationTargetTab)
    : null;
}
