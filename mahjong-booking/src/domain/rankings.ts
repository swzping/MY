import type { Player, RankingPeriod, Result, ResultEntry, Session } from "../types";

export type RecentFormLabel = "手热" | "稳定" | "回暖" | "观察中";
export type RankingEligibilityStatus = "official" | "observation";

export interface PlayerRanking {
  player: Player;
  rank: number | null;
  completedSessionCount: number;
  firstPlaceCount: number;
  winRate: number;
  activityScore: number;
  recentFormLabel: RecentFormLabel;
  currentStreak: number;
  noShowCount: number;
  comprehensiveScore: number;
  eligibilityStatus: RankingEligibilityStatus;
}

interface RankedEntry {
  entry: ResultEntry;
  playedAt: number;
}

const PERIOD_DAYS: Record<RankingPeriod, number | null> = {
  week: 7,
  month: 31,
  all: null,
};

export function buildRankings(
  players: Player[],
  sessions: Session[],
  results: Result[],
  period: RankingPeriod,
  now = new Date(),
): PlayerRanking[] {
  const completedSessionsById = new Map(
    sessions
      .filter((session) => session.status === "completed" && isInPeriod(session.startsAt, period, now))
      .map((session) => [session.id, session]),
  );

  const confirmedResults = results.filter(
    (result) => result.status === "confirmed" && completedSessionsById.has(result.sessionId),
  );

  const entriesByPlayerId = new Map<string, RankedEntry[]>();
  const scoredSessionsById = new Map<string, Session>();

  for (const result of confirmedResults) {
    const session = completedSessionsById.get(result.sessionId);

    if (!session) {
      continue;
    }

    scoredSessionsById.set(session.id, session);

    const playedAt = new Date(session.startsAt).getTime();

    for (const entry of result.entries) {
      const playerEntries = entriesByPlayerId.get(entry.playerId) ?? [];
      playerEntries.push({ entry, playedAt });
      entriesByPlayerId.set(entry.playerId, playerEntries);
    }
  }

  const noShowsByPlayerId = countNoShowsByPlayerId([...scoredSessionsById.values()]);

  const rankings = players.map((player) => {
    const entries = (entriesByPlayerId.get(player.id) ?? []).sort((left, right) => right.playedAt - left.playedAt);
    const completedSessionCount = entries.length;
    const firstPlaceCount = entries.filter(({ entry }) => entry.rank === 1).length;
    const winRate = completedSessionCount > 0 ? firstPlaceCount / completedSessionCount : 0;
    const noShowCount = noShowsByPlayerId.get(player.id) ?? 0;
    const currentStreak = countCurrentStreak(entries);
    const activityScore = Math.min(1, completedSessionCount / 8);
    const recentFormLabel = getRecentFormLabel(entries);
    const recentScore = getRecentScore(entries);
    const streakScore = Math.min(1, currentStreak / 4);
    const comprehensiveScore = Math.max(
      0,
      roundToOneDecimal(winRate * 45 + activityScore * 25 + recentScore * 20 + streakScore * 10 - noShowCount * 8),
    );
    const eligibilityStatus: RankingEligibilityStatus =
      completedSessionCount >= 3 ? "official" : "observation";

    return {
      player,
      rank: null,
      completedSessionCount,
      firstPlaceCount,
      winRate,
      activityScore,
      recentFormLabel,
      currentStreak,
      noShowCount,
      comprehensiveScore,
      eligibilityStatus,
    };
  });

  const officialRankings = rankings
    .filter((ranking) => ranking.eligibilityStatus === "official")
    .sort(compareByScoreThenName)
    .map((ranking, index) => ({ ...ranking, rank: index + 1 }));

  const observationRankings = rankings
    .filter((ranking) => ranking.eligibilityStatus === "observation")
    .sort(compareByScoreThenName);

  return [...officialRankings, ...observationRankings];
}

function isInPeriod(startsAt: string, period: RankingPeriod, now: Date): boolean {
  const periodDays = PERIOD_DAYS[period];
  const timestamp = new Date(startsAt).getTime();

  if (timestamp > now.getTime()) {
    return false;
  }

  if (periodDays === null) {
    return true;
  }

  return timestamp >= now.getTime() - periodDays * 24 * 60 * 60 * 1000;
}

function countNoShowsByPlayerId(sessions: Session[]): Map<string, number> {
  const noShowsByPlayerId = new Map<string, number>();

  for (const session of sessions) {
    for (const playerId of session.noShowPlayerIds) {
      noShowsByPlayerId.set(playerId, (noShowsByPlayerId.get(playerId) ?? 0) + 1);
    }
  }

  return noShowsByPlayerId;
}

function countCurrentStreak(entries: RankedEntry[]): number {
  let streak = 0;

  for (const { entry } of entries) {
    if (entry.rank !== 1) {
      break;
    }

    streak += 1;
  }

  return streak;
}

function getRecentFormLabel(entries: RankedEntry[]): RecentFormLabel {
  if (entries.length < 3) {
    return "观察中";
  }

  const topTwoCount = entries.slice(0, 5).filter(({ entry }) => entry.rank <= 2).length;

  if (topTwoCount >= 4) {
    return "手热";
  }

  if (topTwoCount >= 2) {
    return "稳定";
  }

  return "回暖";
}

function getRecentScore(entries: RankedEntry[]): number {
  const recentEntries = entries.slice(0, 5);

  if (recentEntries.length === 0) {
    return 0;
  }

  return (
    recentEntries.reduce((total, { entry }) => {
      return total + (5 - entry.rank) / 4;
    }, 0) / recentEntries.length
  );
}

function roundToOneDecimal(value: number): number {
  return Math.round(value * 10) / 10;
}

function compareByScoreThenName(left: PlayerRanking, right: PlayerRanking): number {
  if (right.comprehensiveScore !== left.comprehensiveScore) {
    return right.comprehensiveScore - left.comprehensiveScore;
  }

  const displayNameComparison = left.player.displayName.localeCompare(right.player.displayName, "zh-Hans-CN");

  if (displayNameComparison !== 0) {
    return displayNameComparison;
  }

  return left.player.id.localeCompare(right.player.id);
}
