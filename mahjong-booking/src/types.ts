export type SessionStatus =
  | "open"
  | "ready"
  | "inProgress"
  | "pendingResult"
  | "pendingConfirmation"
  | "completed"
  | "cancelled";

export type ResultStatus = "pendingConfirmation" | "confirmed" | "disputed";
export type RankingPeriod = "week" | "month" | "all";
export type TabKey = "home" | "booking" | "results" | "ranking" | "profile";

export interface Player {
  id: string;
  displayName: string;
  avatarColor: string;
  joinedAt: string;
}

export interface Session {
  id: string;
  title: string;
  startsAt: string;
  location: string;
  seatCount: number;
  note: string;
  status: SessionStatus;
  organizerId: string;
  participantIds: string[];
  waitlistIds: string[];
  noShowPlayerIds: string[];
}

export interface ResultEntry {
  playerId: string;
  rank: 1 | 2 | 3 | 4;
  points?: number;
}

export interface Result {
  id: string;
  sessionId: string;
  entries: ResultEntry[];
  submittedBy: string;
  submittedAt: string;
  confirmationPlayerIds: string[];
  status: ResultStatus;
}
