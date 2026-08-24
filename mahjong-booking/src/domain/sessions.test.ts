import { describe, expect, it } from "vitest";

import type { Session } from "../types";
import { cancelSeat, joinSession } from "./sessions";

const openSession: Session = {
  id: "s1",
  title: "今晚开桌",
  startsAt: "2026-07-23T20:00:00+08:00",
  location: "老地方",
  seatCount: 4,
  note: "",
  status: "open",
  organizerId: "a",
  participantIds: ["a", "b", "c"],
  waitlistIds: [],
  noShowPlayerIds: [],
};

describe("session transitions", () => {
  it("adds a player and marks the session ready when seats fill", () => {
    const session = joinSession(openSession, "d");

    expect(session.participantIds).toEqual(["a", "b", "c", "d"]);
    expect(session.waitlistIds).toEqual([]);
    expect(session.status).toBe("ready");
  });

  it("adds an extra player to the waitlist when full and leaves participants unchanged", () => {
    const fullSession = joinSession(openSession, "d");

    const session = joinSession(fullSession, "e");

    expect(session.participantIds).toEqual(["a", "b", "c", "d"]);
    expect(session.waitlistIds).toEqual(["e"]);
    expect(session.status).toBe("ready");
  });

  it("leaves duplicate participant and waitlisted joins unchanged", () => {
    const waitlistedSession: Session = {
      ...openSession,
      status: "ready",
      participantIds: ["a", "b", "c", "d"],
      waitlistIds: ["e"],
    };

    expect(joinSession(waitlistedSession, "a")).toBe(waitlistedSession);
    expect(joinSession(waitlistedSession, "e")).toBe(waitlistedSession);
  });

  it("returns completed sessions unchanged when a player tries to join", () => {
    const completedSession: Session = {
      ...openSession,
      status: "completed",
    };

    expect(joinSession(completedSession, "d")).toBe(completedSession);
  });

  it("removes a waitlisted player when they cancel", () => {
    const waitlistedSession: Session = {
      ...openSession,
      status: "ready",
      participantIds: ["a", "b", "c", "d"],
      waitlistIds: ["e", "f"],
    };

    const session = cancelSeat(waitlistedSession, "e");

    expect(session.participantIds).toEqual(["a", "b", "c", "d"]);
    expect(session.waitlistIds).toEqual(["f"]);
    expect(session.status).toBe("ready");
  });

  it("returns the original session when an unknown player cancels", () => {
    const session = cancelSeat(openSession, "z");

    expect(session).toBe(openSession);
  });

  it("returns completed sessions unchanged when a player tries to cancel", () => {
    const completedSession: Session = {
      ...openSession,
      status: "completed",
    };

    expect(cancelSeat(completedSession, "a")).toBe(completedSession);
  });

  it("opens a full session when a participant cancels without a waitlist", () => {
    const fullSession: Session = {
      ...openSession,
      status: "ready",
      participantIds: ["a", "b", "c", "d"],
    };

    const session = cancelSeat(fullSession, "d");

    expect(session.participantIds).toEqual(["a", "b", "c"]);
    expect(session.waitlistIds).toEqual([]);
    expect(session.status).toBe("open");
  });

  it("promotes the first waitlisted player after cancellation and keeps the session ready", () => {
    const waitlistedSession: Session = {
      ...openSession,
      status: "ready",
      participantIds: ["a", "b", "c", "d"],
      waitlistIds: ["e"],
    };

    const session = cancelSeat(waitlistedSession, "b");

    expect(session.participantIds).toEqual(["a", "c", "d", "e"]);
    expect(session.waitlistIds).toEqual([]);
    expect(session.status).toBe("ready");
  });

  it("does not mutate input arrays during real transitions", () => {
    const session = joinSession(openSession, "d");

    expect(session).not.toBe(openSession);
    expect(session.participantIds).not.toBe(openSession.participantIds);
    expect(session.waitlistIds).toBe(openSession.waitlistIds);
    expect(openSession.participantIds).toEqual(["a", "b", "c"]);
    expect(openSession.waitlistIds).toEqual([]);
  });

  it("does not mutate input arrays when cancellation promotes a waitlisted player", () => {
    const waitlistedSession: Session = {
      ...openSession,
      status: "ready",
      participantIds: ["a", "b", "c", "d"],
      waitlistIds: ["e", "f"],
    };

    const session = cancelSeat(waitlistedSession, "b");

    expect(session).not.toBe(waitlistedSession);
    expect(session.participantIds).not.toBe(waitlistedSession.participantIds);
    expect(session.waitlistIds).not.toBe(waitlistedSession.waitlistIds);
    expect(session.participantIds).toEqual(["a", "c", "d", "e"]);
    expect(session.waitlistIds).toEqual(["f"]);
    expect(waitlistedSession.participantIds).toEqual(["a", "b", "c", "d"]);
    expect(waitlistedSession.waitlistIds).toEqual(["e", "f"]);
  });
});
