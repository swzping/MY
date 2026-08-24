import { describe, expect, it } from "vitest";
import type { Player, Result, Session } from "../types";
import { buildRankings } from "./rankings";

const now = new Date("2026-07-23T12:00:00+08:00");

const players: Player[] = [
  { id: "a", displayName: "阿杰", avatarColor: "#dc3f2f", joinedAt: "2026-06-01" },
  { id: "b", displayName: "小林", avatarColor: "#1f6650", joinedAt: "2026-06-03" },
  { id: "c", displayName: "老周", avatarColor: "#e7b84b", joinedAt: "2026-06-08" },
];

const sessions: Session[] = [
  {
    id: "s1",
    title: "周一局",
    startsAt: "2026-07-17T20:00:00+08:00",
    location: "茶室",
    seatCount: 4,
    note: "",
    status: "completed",
    organizerId: "a",
    participantIds: ["a", "b"],
    waitlistIds: [],
    noShowPlayerIds: [],
  },
  {
    id: "s2",
    title: "周二局",
    startsAt: "2026-07-19T20:00:00+08:00",
    location: "茶室",
    seatCount: 4,
    note: "",
    status: "completed",
    organizerId: "b",
    participantIds: ["a", "b"],
    waitlistIds: [],
    noShowPlayerIds: [],
  },
  {
    id: "s3",
    title: "周三局",
    startsAt: "2026-07-21T20:00:00+08:00",
    location: "茶室",
    seatCount: 4,
    note: "",
    status: "completed",
    organizerId: "a",
    participantIds: ["a", "b"],
    waitlistIds: [],
    noShowPlayerIds: ["b"],
  },
];

const results: Result[] = [
  {
    id: "r1",
    sessionId: "s1",
    submittedBy: "a",
    submittedAt: "2026-07-17T23:00:00+08:00",
    confirmationPlayerIds: ["a", "b"],
    status: "confirmed",
    entries: [
      { playerId: "a", rank: 1 },
      { playerId: "b", rank: 2 },
    ],
  },
  {
    id: "r2",
    sessionId: "s2",
    submittedBy: "b",
    submittedAt: "2026-07-19T23:00:00+08:00",
    confirmationPlayerIds: ["a", "b"],
    status: "confirmed",
    entries: [
      { playerId: "b", rank: 1 },
      { playerId: "a", rank: 2 },
    ],
  },
  {
    id: "r3",
    sessionId: "s3",
    submittedBy: "a",
    submittedAt: "2026-07-21T23:00:00+08:00",
    confirmationPlayerIds: ["a", "b"],
    status: "confirmed",
    entries: [
      { playerId: "a", rank: 1 },
      { playerId: "b", rank: 4 },
    ],
  },
];

describe("buildRankings", () => {
  it("calculates official ranking metrics from confirmed completed sessions", () => {
    const rankings = buildRankings(players, sessions, results, "week", now);

    const ajie = rankings.find((ranking) => ranking.player.id === "a");
    const laozhou = rankings.find((ranking) => ranking.player.id === "c");

    expect(ajie).toMatchObject({
      completedSessionCount: 3,
      firstPlaceCount: 2,
      eligibilityStatus: "official",
      recentFormLabel: "稳定",
      currentStreak: 1,
    });
    expect(ajie?.winRate).toBeCloseTo(0.667, 3);
    expect(ajie?.rank).toBe(1);

    expect(laozhou).toMatchObject({
      completedSessionCount: 0,
      firstPlaceCount: 0,
      winRate: 0,
      eligibilityStatus: "observation",
      rank: null,
    });
  });

  it("penalizes no-shows in the comprehensive score", () => {
    const rankings = buildRankings(players, sessions, results, "week", now);

    const ajie = rankings.find((ranking) => ranking.player.id === "a");
    const xiaolin = rankings.find((ranking) => ranking.player.id === "b");

    expect(xiaolin?.noShowCount).toBe(1);
    expect(ajie?.comprehensiveScore).toBeGreaterThan(xiaolin?.comprehensiveScore ?? 0);
  });

  it("excludes pending and disputed results from metrics and no-show penalties", () => {
    const extraSessions: Session[] = [
      {
        ...sessions[0],
        id: "pending-session",
        startsAt: "2026-07-22T20:00:00+08:00",
        noShowPlayerIds: ["a"],
      },
      {
        ...sessions[0],
        id: "disputed-session",
        startsAt: "2026-07-22T21:00:00+08:00",
        noShowPlayerIds: ["b"],
      },
    ];
    const extraResults: Result[] = [
      {
        ...results[0],
        id: "pending-result",
        sessionId: "pending-session",
        status: "pendingConfirmation",
      },
      {
        ...results[0],
        id: "disputed-result",
        sessionId: "disputed-session",
        status: "disputed",
      },
    ];

    const rankings = buildRankings(players, [...sessions, ...extraSessions], [...results, ...extraResults], "week", now);

    expect(rankings.find((ranking) => ranking.player.id === "a")).toMatchObject({
      completedSessionCount: 3,
      firstPlaceCount: 2,
      noShowCount: 0,
    });
    expect(rankings.find((ranking) => ranking.player.id === "b")).toMatchObject({
      completedSessionCount: 3,
      firstPlaceCount: 1,
      noShowCount: 1,
    });
  });

  it("excludes incomplete sessions even when they have confirmed results", () => {
    const inProgressSession: Session = {
      ...sessions[0],
      id: "in-progress-session",
      status: "inProgress",
      startsAt: "2026-07-22T20:00:00+08:00",
      noShowPlayerIds: ["a"],
    };
    const inProgressResult: Result = {
      ...results[0],
      id: "in-progress-result",
      sessionId: inProgressSession.id,
    };

    const rankings = buildRankings(players, [...sessions, inProgressSession], [...results, inProgressResult], "week", now);

    expect(rankings.find((ranking) => ranking.player.id === "a")).toMatchObject({
      completedSessionCount: 3,
      firstPlaceCount: 2,
      noShowCount: 0,
    });
  });

  it("uses the explicit now value for rolling period windows", () => {
    const rankings = buildRankings(players, sessions, results, "week", new Date("2026-07-20T12:00:00+08:00"));

    expect(rankings.find((ranking) => ranking.player.id === "a")).toMatchObject({
      completedSessionCount: 2,
      firstPlaceCount: 1,
      eligibilityStatus: "observation",
      rank: null,
    });
    expect(rankings.find((ranking) => ranking.player.id === "b")?.noShowCount).toBe(0);
  });
});
