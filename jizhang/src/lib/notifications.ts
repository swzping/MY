import notifee, {
  AndroidImportance,
  EventType,
  TimeUnit,
  TriggerType,
} from "@notifee/react-native";
import { Platform } from "react-native";
import {
  getNotificationTargetTab,
  type NotificationTargetTab,
} from "./notificationRouting";

const reminderNotificationId = "half-hour-record-reminder";
const reminderChannelId = "budget-reminders";

async function ensureReminderChannel() {
  if (Platform.OS !== "android") {
    return undefined;
  }

  return notifee.createChannel({
    id: reminderChannelId,
    name: "记账提醒",
    importance: AndroidImportance.DEFAULT,
  });
}

export async function scheduleHalfHourRecordReminder() {
  await notifee.requestPermission();
  const channelId = await ensureReminderChannel();

  await notifee.cancelTriggerNotification(reminderNotificationId);
  await notifee.createTriggerNotification(
    {
      id: reminderNotificationId,
      title: "记账提醒",
      body: "花半分钟记录一下刚才的收支吧",
      data: { targetTab: "record" },
      android: channelId
        ? {
            channelId,
            pressAction: { id: "default" },
          }
        : undefined,
    },
    {
      type: TriggerType.TIMESTAMP,
      timestamp: Date.now() + 30 * 1000,
    },
  );
}

export function subscribeToNotificationPress(onTargetTab: (tab: NotificationTargetTab) => void) {
  return notifee.onForegroundEvent(({ type, detail }) => {
    if (type !== EventType.PRESS) {
      return;
    }

    const targetTab = getNotificationTargetTab(detail.notification?.data);
    if (targetTab) {
      onTargetTab(targetTab);
    }
  });
}

export async function handleInitialNotification(onTargetTab: (tab: NotificationTargetTab) => void) {
  const initialNotification = await notifee.getInitialNotification();
  const targetTab = getNotificationTargetTab(initialNotification?.notification.data);

  if (targetTab) {
    onTargetTab(targetTab);
  }
}
