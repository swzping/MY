import { describe, expect, it } from "vitest";
import { getNotificationTargetTab } from "./notificationRouting";

describe("notification routing", () => {
  it("returns the target tab when notification data contains a supported tab", () => {
    expect(getNotificationTargetTab({ targetTab: "record" })).toBe("record");
  });

  it("ignores missing, non-string, or unsupported target tabs", () => {
    expect(getNotificationTargetTab(undefined)).toBeNull();
    expect(getNotificationTargetTab({ targetTab: 123 })).toBeNull();
    expect(getNotificationTargetTab({ targetTab: "settings" })).toBeNull();
  });
});
