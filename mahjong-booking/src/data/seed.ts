import type { Player, Result, Session } from "../types";

export const players: Player[] = [
  { id: "ajie", displayName: "阿杰", avatarColor: "#dc3f2f", joinedAt: "2026-06-01" },
  { id: "xiaolin", displayName: "小林", avatarColor: "#1f6650", joinedAt: "2026-06-03" },
  { id: "laozhou", displayName: "老周", avatarColor: "#e7b84b", joinedAt: "2026-06-08" },
  { id: "momo", displayName: "莫莫", avatarColor: "#356d8c", joinedAt: "2026-06-10" },
  { id: "anan", displayName: "安安", avatarColor: "#8e5a3c", joinedAt: "2026-06-18" },
  { id: "dali", displayName: "大力", avatarColor: "#694f8e", joinedAt: "2026-06-20" }
];

export const sessions: Session[] = [
  {
    id: "session-tonight",
    title: "今晚开桌",
    startsAt: "2026-07-23T20:00:00+08:00",
    location: "老地方茶室",
    seatCount: 4,
    note: "三缺一，带点夜宵。",
    status: "open",
    organizerId: "ajie",
    participantIds: ["ajie", "xiaolin", "laozhou"],
    waitlistIds: [],
    noShowPlayerIds: []
  },
  {
    id: "session-1",
    title: "周二小局",
    startsAt: "2026-07-21T20:00:00+08:00",
    location: "小林家",
    seatCount: 4,
    note: "东南风两圈。",
    status: "completed",
    organizerId: "xiaolin",
    participantIds: ["ajie", "xiaolin", "laozhou", "momo"],
    waitlistIds: [],
    noShowPlayerIds: []
  },
  {
    id: "session-2",
    title: "周末局",
    startsAt: "2026-07-19T14:30:00+08:00",
    location: "社区活动室",
    seatCount: 4,
    note: "下午场。",
    status: "completed",
    organizerId: "laozhou",
    participantIds: ["ajie", "xiaolin", "momo", "dali"],
    waitlistIds: [],
    noShowPlayerIds: ["anan"]
  },
  {
    id: "session-3",
    title: "夜宵局",
    startsAt: "2026-07-17T21:00:00+08:00",
    location: "老地方茶室",
    seatCount: 4,
    note: "打完吃粉。",
    status: "completed",
    organizerId: "momo",
    participantIds: ["ajie", "xiaolin", "laozhou", "dali"],
    waitlistIds: [],
    noShowPlayerIds: []
  }
];

export const results: Result[] = [
  {
    id: "result-1",
    sessionId: "session-1",
    submittedBy: "xiaolin",
    submittedAt: "2026-07-21T23:30:00+08:00",
    status: "confirmed",
    confirmationPlayerIds: ["ajie", "xiaolin", "laozhou", "momo"],
    entries: [
      { playerId: "ajie", rank: 1, points: 42 },
      { playerId: "xiaolin", rank: 2, points: 16 },
      { playerId: "momo", rank: 3, points: -12 },
      { playerId: "laozhou", rank: 4, points: -46 }
    ]
  },
  {
    id: "result-2",
    sessionId: "session-2",
    submittedBy: "laozhou",
    submittedAt: "2026-07-19T18:10:00+08:00",
    status: "confirmed",
    confirmationPlayerIds: ["ajie", "xiaolin", "momo", "dali"],
    entries: [
      { playerId: "xiaolin", rank: 1, points: 35 },
      { playerId: "ajie", rank: 2, points: 10 },
      { playerId: "momo", rank: 3, points: -14 },
      { playerId: "dali", rank: 4, points: -31 }
    ]
  },
  {
    id: "result-3",
    sessionId: "session-3",
    submittedBy: "momo",
    submittedAt: "2026-07-18T00:25:00+08:00",
    status: "confirmed",
    confirmationPlayerIds: ["ajie", "xiaolin", "laozhou", "dali"],
    entries: [
      { playerId: "ajie", rank: 1, points: 51 },
      { playerId: "dali", rank: 2, points: 8 },
      { playerId: "xiaolin", rank: 3, points: -19 },
      { playerId: "laozhou", rank: 4, points: -40 }
    ]
  }
];
