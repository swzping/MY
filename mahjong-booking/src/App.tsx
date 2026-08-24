import { useMemo, useState } from "react";
import { CalendarDays, ClipboardList, HomeIcon, Trophy, UserRound } from "lucide-react";

import { Booking } from "./components/Booking";
import type { CreateSessionDraft } from "./components/Booking";
import { Home } from "./components/Home";
import { Profile } from "./components/Profile";
import { Ranking } from "./components/Ranking";
import { Results } from "./components/Results";
import { players as seedPlayers, results as seedResults, sessions as seedSessions } from "./data/seed";
import { buildRankings } from "./domain/rankings";
import { cancelSeat, joinSession } from "./domain/sessions";
import type { RankingPeriod, Result, Session, TabKey } from "./types";

const tabs: Array<{
  key: TabKey;
  label: string;
  Icon: typeof HomeIcon;
}> = [
  { key: "home", label: "首页", Icon: HomeIcon },
  { key: "booking", label: "约局", Icon: CalendarDays },
  { key: "results", label: "战绩", Icon: ClipboardList },
  { key: "ranking", label: "排行", Icon: Trophy },
  { key: "profile", label: "我的", Icon: UserRound },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("home");
  const [sessions, setSessions] = useState<Session[]>(seedSessions);
  const [results, setResults] = useState<Result[]>(seedResults);
  const [rankingPeriod, setRankingPeriod] = useState<RankingPeriod>("all");
  const rankings = useMemo(
    () => buildRankings(seedPlayers, sessions, results, rankingPeriod),
    [sessions, results, rankingPeriod],
  );

  function updateSession(sessionId: string, updater: (session: Session) => Session) {
    setSessions((current) => current.map((session) => (session.id === sessionId ? updater(session) : session)));
  }

  function createSession(draft: CreateSessionDraft) {
    const currentPlayer = seedPlayers[4];
    const session: Session = {
      id: `session-${Date.now()}`,
      title: "新约局",
      startsAt: draft.startsAt,
      location: draft.location,
      seatCount: draft.seatCount,
      note: draft.note || "朋友局",
      status: "open",
      organizerId: currentPlayer?.id ?? seedPlayers[0].id,
      participantIds: currentPlayer ? [currentPlayer.id] : [],
      waitlistIds: [],
      noShowPlayerIds: [],
    };

    setSessions((current) => [session, ...current]);
  }

  function submitResult(sessionId: string, orderedPlayerIds: string[]) {
    const session = sessions.find((item) => item.id === sessionId);
    const participantIds = session?.participantIds ?? [];

    if (
      !session ||
      session.status !== "ready" ||
      orderedPlayerIds.length !== session.seatCount ||
      new Set(orderedPlayerIds).size !== orderedPlayerIds.length ||
      orderedPlayerIds.some((playerId) => !participantIds.includes(playerId))
    ) {
      return;
    }

    const rankPoints = [42, 16, -12, -46];
    const result: Result = {
      id: `result-${Date.now()}`,
      sessionId,
      submittedBy: seedPlayers[0].id,
      submittedAt: new Date().toISOString(),
      status: "confirmed",
      confirmationPlayerIds: orderedPlayerIds,
      entries: orderedPlayerIds.map((playerId, index) => ({
        playerId,
        rank: (index + 1) as 1 | 2 | 3 | 4,
        points: rankPoints[index],
      })),
    };

    setResults((current) => [result, ...current]);
    updateSession(sessionId, (session) => ({
      ...session,
      status: "completed",
      participantIds: orderedPlayerIds,
      waitlistIds: [],
    }));
  }

  const screen = {
    home: (
      <Home
        currentPlayer={seedPlayers[4]}
        players={seedPlayers}
        sessions={sessions}
        rankings={rankings}
        onJoin={(sessionId, playerId) => updateSession(sessionId, (session) => joinSession(session, playerId))}
      />
    ),
    booking: (
      <Booking
        currentPlayer={seedPlayers[4]}
        players={seedPlayers}
        sessions={sessions}
        onCreate={createSession}
        onJoin={(sessionId, playerId) => updateSession(sessionId, (session) => joinSession(session, playerId))}
        onCancel={(sessionId, playerId) => updateSession(sessionId, (session) => cancelSeat(session, playerId))}
      />
    ),
    results: (
      <Results
        currentPlayer={seedPlayers[0]}
        players={seedPlayers}
        sessions={sessions}
        results={results}
        onSubmitResult={submitResult}
      />
    ),
    ranking: <Ranking period={rankingPeriod} rankings={rankings} onPeriodChange={setRankingPeriod} />,
    profile: <Profile ranking={rankings.find((ranking) => ranking.player.id === "ajie") ?? rankings[0]} />,
  }[activeTab];

  return (
    <main className="app-shell">
      <section className="phone-frame">
        <header className="top-bar">
          <div>
            <p className="eyebrow">朋友局小程序</p>
            <h1>雀友局</h1>
          </div>
          <span className="season-pill">成员 {seedPlayers.length} 人</span>
        </header>
        <section className="screen-body">{screen}</section>
        <nav className="tab-bar" aria-label="主导航">
          {tabs.map((tab) => {
            const { Icon } = tab;
            const isActive = activeTab === tab.key;

            return (
              <button
                key={tab.key}
                aria-current={isActive ? "page" : undefined}
                className={isActive ? "tab-button active" : "tab-button"}
                type="button"
                onClick={() => setActiveTab(tab.key)}
              >
                <Icon aria-hidden="true" size={20} strokeWidth={2.1} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </section>
    </main>
  );
}
