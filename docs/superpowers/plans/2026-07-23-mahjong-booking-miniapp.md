# Mahjong Booking Miniapp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a polished mobile-first mahjong friend-game booking prototype with session signup, lightweight result entry, player stats, and playful rankings.

**Architecture:** Create a standalone React + Vite + TypeScript app in `mahjong-booking/`. Keep domain logic in pure TypeScript modules with Vitest coverage, and keep React components focused on rendering and local state transitions. Use seeded in-memory data for version one so the prototype is immediately runnable without a backend.

**Tech Stack:** React 18, Vite, TypeScript, Vitest, lucide-react, CSS modules through plain `src/styles.css`.

---

## File Structure

- Create `mahjong-booking/package.json`: scripts and dependencies for the standalone prototype.
- Create `mahjong-booking/index.html`: Vite HTML entry.
- Create `mahjong-booking/tsconfig.json`: TypeScript browser configuration.
- Create `mahjong-booking/vite.config.ts`: Vite + React + Vitest configuration.
- Create `mahjong-booking/src/main.tsx`: React bootstrap.
- Create `mahjong-booking/src/App.tsx`: app shell, tab navigation, and shared state.
- Create `mahjong-booking/src/types.ts`: domain types for players, sessions, results, rankings, and tabs.
- Create `mahjong-booking/src/data/seed.ts`: seeded players, sessions, and results.
- Create `mahjong-booking/src/domain/rankings.ts`: pure ranking/stat calculations.
- Create `mahjong-booking/src/domain/sessions.ts`: pure session transition helpers.
- Create `mahjong-booking/src/domain/rankings.test.ts`: ranking calculation tests.
- Create `mahjong-booking/src/domain/sessions.test.ts`: session transition tests.
- Create `mahjong-booking/src/components/Home.tsx`: next-session hero and leaderboard highlights.
- Create `mahjong-booking/src/components/Booking.tsx`: create session, join, cancel, and waitlist UI.
- Create `mahjong-booking/src/components/Results.tsx`: rank-based result entry and confirmation UI.
- Create `mahjong-booking/src/components/Ranking.tsx`: leaderboard tabs and observation section.
- Create `mahjong-booking/src/components/Profile.tsx`: personal stat card and history.
- Create `mahjong-booking/src/styles.css`: mobile-first visual system and responsive layout.

## Task 1: Scaffold The Standalone Prototype

**Files:**
- Create: `mahjong-booking/package.json`
- Create: `mahjong-booking/index.html`
- Create: `mahjong-booking/tsconfig.json`
- Create: `mahjong-booking/vite.config.ts`
- Create: `mahjong-booking/src/main.tsx`
- Create: `mahjong-booking/src/App.tsx`
- Create: `mahjong-booking/src/styles.css`

- [ ] **Step 1: Create package scripts and dependencies**

Write `mahjong-booking/package.json`:

```json
{
  "name": "mahjong-booking",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1 --port 5178",
    "build": "tsc -b && vite build",
    "preview": "vite preview --host 127.0.0.1 --port 4178",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.4.1",
    "lucide-react": "^0.511.0",
    "vite": "^6.3.5",
    "typescript": "~5.8.3",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "vitest": "^3.0.0"
  }
}
```

- [ ] **Step 2: Create the Vite entry files**

Write `mahjong-booking/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>雀友局</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Write `mahjong-booking/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "references": []
}
```

Write `mahjong-booking/vite.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "node",
    globals: true,
  },
});
```

- [ ] **Step 3: Add the first app shell**

Write `mahjong-booking/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

Write `mahjong-booking/src/App.tsx`:

```tsx
export default function App() {
  return (
    <main className="app-shell">
      <section className="phone-frame">
        <header className="top-bar">
          <div>
            <p className="eyebrow">朋友局小程序</p>
            <h1>雀友局</h1>
          </div>
          <span className="season-pill">本周第 3 场</span>
        </header>
        <section className="empty-state">
          <h2>今晚能不能开桌，一眼就知道。</h2>
          <p>下一步会接入约局、战绩和排行榜数据。</p>
        </section>
      </section>
    </main>
  );
}
```

Write `mahjong-booking/src/styles.css`:

```css
:root {
  font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #29251f;
  background: #203f35;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
}

button {
  font: inherit;
}

.app-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at 15% 10%, rgba(231, 184, 75, 0.22), transparent 28%),
    linear-gradient(145deg, #203f35 0%, #153328 100%);
}

.phone-frame {
  width: min(430px, 100%);
  min-height: 760px;
  background: #f6f0e4;
  border: 1px solid #29251f;
  box-shadow: 0 22px 70px rgba(0, 0, 0, 0.34);
  overflow: hidden;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 18px;
  border-bottom: 1px solid #29251f;
}

.eyebrow {
  margin: 0 0 3px;
  color: #776a5b;
  font-size: 12px;
}

h1,
h2,
p {
  margin: 0;
}

h1 {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 28px;
}

.season-pill {
  background: #1f6650;
  color: #fff;
  border-radius: 999px;
  padding: 7px 10px;
  font-size: 12px;
  white-space: nowrap;
}

.empty-state {
  padding: 28px 18px;
}

.empty-state h2 {
  font-size: 26px;
  line-height: 1.18;
}

.empty-state p {
  margin-top: 10px;
  color: #776a5b;
}
```

- [ ] **Step 4: Install dependencies and verify the shell builds**

Run:

```bash
cd mahjong-booking
npm install
npm run build
```

Expected: `vite build` completes and creates `mahjong-booking/dist`.

- [ ] **Step 5: Commit the scaffold**

Run:

```bash
git add mahjong-booking
git commit -m "feat: scaffold mahjong booking prototype"
```

Expected: commit succeeds with the new app shell.

## Task 2: Add Domain Types And Seed Data

**Files:**
- Create: `mahjong-booking/src/types.ts`
- Create: `mahjong-booking/src/data/seed.ts`
- Modify: `mahjong-booking/src/App.tsx`

- [ ] **Step 1: Add domain types**

Write `mahjong-booking/src/types.ts`:

```ts
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
```

- [ ] **Step 2: Add seed data**

Write `mahjong-booking/src/data/seed.ts`:

```ts
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
    participantIds: ["ajie", "xiaolin", "momo", "anan"],
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
    confirmationPlayerIds: ["ajie", "xiaolin", "momo", "anan"],
    entries: [
      { playerId: "xiaolin", rank: 1, points: 35 },
      { playerId: "ajie", rank: 2, points: 10 },
      { playerId: "momo", rank: 3, points: -14 },
      { playerId: "anan", rank: 4, points: -31 }
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
```

- [ ] **Step 3: Wire seed data into the app shell**

Modify `mahjong-booking/src/App.tsx`:

```tsx
import { players, sessions } from "./data/seed";

export default function App() {
  const nextSession = sessions.find((session) => session.status === "open" || session.status === "ready");

  return (
    <main className="app-shell">
      <section className="phone-frame">
        <header className="top-bar">
          <div>
            <p className="eyebrow">朋友局小程序</p>
            <h1>雀友局</h1>
          </div>
          <span className="season-pill">成员 {players.length} 人</span>
        </header>
        <section className="empty-state">
          <h2>{nextSession ? nextSession.title : "今晚能不能开桌，一眼就知道。"}</h2>
          <p>{nextSession ? `${nextSession.location} · ${nextSession.participantIds.length}/${nextSession.seatCount}` : "暂无约局。"}</p>
        </section>
      </section>
    </main>
  );
}
```

- [ ] **Step 4: Run typecheck through build**

Run:

```bash
cd mahjong-booking
npm run build
```

Expected: TypeScript and Vite build pass.

- [ ] **Step 5: Commit domain seed data**

Run:

```bash
git add mahjong-booking/src
git commit -m "feat: add mahjong domain seed data"
```

Expected: commit includes `types.ts`, `data/seed.ts`, and the updated `App.tsx`.

## Task 3: Implement Ranking Calculations With Tests

**Files:**
- Create: `mahjong-booking/src/domain/rankings.ts`
- Create: `mahjong-booking/src/domain/rankings.test.ts`

- [ ] **Step 1: Write failing ranking tests**

Write `mahjong-booking/src/domain/rankings.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import type { Player, Result, Session } from "../types";
import { buildRankings } from "./rankings";

const players: Player[] = [
  { id: "a", displayName: "阿杰", avatarColor: "#dc3f2f", joinedAt: "2026-06-01" },
  { id: "b", displayName: "小林", avatarColor: "#1f6650", joinedAt: "2026-06-01" },
  { id: "c", displayName: "老周", avatarColor: "#e7b84b", joinedAt: "2026-06-01" }
];

const sessions: Session[] = [
  { id: "s1", title: "一", startsAt: "2026-07-01T20:00:00+08:00", location: "A", seatCount: 4, note: "", status: "completed", organizerId: "a", participantIds: ["a", "b"], waitlistIds: [], noShowPlayerIds: [] },
  { id: "s2", title: "二", startsAt: "2026-07-02T20:00:00+08:00", location: "A", seatCount: 4, note: "", status: "completed", organizerId: "a", participantIds: ["a", "b"], waitlistIds: [], noShowPlayerIds: [] },
  { id: "s3", title: "三", startsAt: "2026-07-03T20:00:00+08:00", location: "A", seatCount: 4, note: "", status: "completed", organizerId: "a", participantIds: ["a", "b"], waitlistIds: [], noShowPlayerIds: ["b"] }
];

const results: Result[] = [
  { id: "r1", sessionId: "s1", submittedBy: "a", submittedAt: "2026-07-01T23:00:00+08:00", confirmationPlayerIds: ["a", "b"], status: "confirmed", entries: [{ playerId: "a", rank: 1 }, { playerId: "b", rank: 2 }] },
  { id: "r2", sessionId: "s2", submittedBy: "a", submittedAt: "2026-07-02T23:00:00+08:00", confirmationPlayerIds: ["a", "b"], status: "confirmed", entries: [{ playerId: "b", rank: 1 }, { playerId: "a", rank: 2 }] },
  { id: "r3", sessionId: "s3", submittedBy: "a", submittedAt: "2026-07-03T23:00:00+08:00", confirmationPlayerIds: ["a", "b"], status: "confirmed", entries: [{ playerId: "a", rank: 1 }, { playerId: "b", rank: 2 }] }
];

describe("buildRankings", () => {
  it("calculates win rate and official eligibility", () => {
    const rankings = buildRankings(players, sessions, results, "all");
    const ajie = rankings.find((ranking) => ranking.player.id === "a");

    expect(ajie?.completedSessionCount).toBe(3);
    expect(ajie?.firstPlaceCount).toBe(2);
    expect(ajie?.winRate).toBeCloseTo(0.667, 3);
    expect(ajie?.eligibilityStatus).toBe("official");
  });

  it("keeps players with fewer than three sessions in observation", () => {
    const rankings = buildRankings(players, sessions, results, "all");
    const laozhou = rankings.find((ranking) => ranking.player.id === "c");

    expect(laozhou?.completedSessionCount).toBe(0);
    expect(laozhou?.eligibilityStatus).toBe("observation");
  });

  it("penalizes no-shows in comprehensive score", () => {
    const rankings = buildRankings(players, sessions, results, "all");
    const ajie = rankings.find((ranking) => ranking.player.id === "a");
    const xiaolin = rankings.find((ranking) => ranking.player.id === "b");

    expect((ajie?.comprehensiveScore ?? 0) > (xiaolin?.comprehensiveScore ?? 0)).toBe(true);
    expect(xiaolin?.noShowCount).toBe(1);
  });
});
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
cd mahjong-booking
npm test -- src/domain/rankings.test.ts
```

Expected: FAIL because `./rankings` does not exist.

- [ ] **Step 3: Implement ranking logic**

Write `mahjong-booking/src/domain/rankings.ts`:

```ts
import type { Player, RankingPeriod, Result, Session } from "../types";

export interface PlayerRanking {
  player: Player;
  rank: number | null;
  completedSessionCount: number;
  firstPlaceCount: number;
  winRate: number;
  activityScore: number;
  recentFormLabel: "手热" | "稳定" | "回暖" | "观察中";
  currentStreak: number;
  noShowCount: number;
  comprehensiveScore: number;
  eligibilityStatus: "official" | "observation";
}

const PERIOD_DAYS: Record<RankingPeriod, number | null> = {
  week: 7,
  month: 31,
  all: null
};

export function buildRankings(
  players: Player[],
  sessions: Session[],
  results: Result[],
  period: RankingPeriod,
  now = new Date("2026-07-23T12:00:00+08:00"),
): PlayerRanking[] {
  const periodStart = getPeriodStart(period, now);
  const sessionsById = new Map(sessions.map((session) => [session.id, session]));
  const confirmedResults = results.filter((result) => result.status === "confirmed");
  const periodResults = confirmedResults.filter((result) => {
    const session = sessionsById.get(result.sessionId);
    return session?.status === "completed" && (!periodStart || new Date(session.startsAt) >= periodStart);
  });

  const rankings = players.map((player) => {
    const playerResults = periodResults
      .filter((result) => result.entries.some((entry) => entry.playerId === player.id))
      .sort((left, right) => {
        const leftSession = sessionsById.get(left.sessionId);
        const rightSession = sessionsById.get(right.sessionId);
        return new Date(leftSession?.startsAt ?? 0).getTime() - new Date(rightSession?.startsAt ?? 0).getTime();
      });

    const completedSessionCount = playerResults.length;
    const firstPlaceCount = playerResults.filter((result) =>
      result.entries.some((entry) => entry.playerId === player.id && entry.rank === 1),
    ).length;
    const winRate = completedSessionCount === 0 ? 0 : firstPlaceCount / completedSessionCount;
    const noShowCount = sessions.filter((session) =>
      session.noShowPlayerIds.includes(player.id) && (!periodStart || new Date(session.startsAt) >= periodStart),
    ).length;
    const currentStreak = getCurrentFirstPlaceStreak(player.id, playerResults);
    const activityScore = Math.min(1, completedSessionCount / 8);
    const recentFormLabel = getRecentFormLabel(player.id, playerResults);
    const recentScore = getRecentScore(player.id, playerResults);
    const streakScore = Math.min(1, currentStreak / 4);
    const comprehensiveScore = Math.max(
      0,
      Math.round((winRate * 45 + activityScore * 25 + recentScore * 20 + streakScore * 10 - noShowCount * 8) * 10) / 10,
    );

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
      eligibilityStatus: completedSessionCount >= 3 ? "official" : "observation"
    };
  });

  const official = rankings
    .filter((ranking) => ranking.eligibilityStatus === "official")
    .sort((left, right) => right.comprehensiveScore - left.comprehensiveScore)
    .map((ranking, index) => ({ ...ranking, rank: index + 1 }));

  const observation = rankings
    .filter((ranking) => ranking.eligibilityStatus === "observation")
    .sort((left, right) => right.comprehensiveScore - left.comprehensiveScore);

  return [...official, ...observation];
}

function getPeriodStart(period: RankingPeriod, now: Date) {
  const days = PERIOD_DAYS[period];
  if (!days) return null;
  const start = new Date(now);
  start.setDate(start.getDate() - days);
  return start;
}

function getCurrentFirstPlaceStreak(playerId: string, results: Result[]) {
  let streak = 0;
  for (const result of [...results].reverse()) {
    const entry = result.entries.find((item) => item.playerId === playerId);
    if (entry?.rank === 1) {
      streak += 1;
    } else {
      break;
    }
  }
  return streak;
}

function getRecentFormLabel(playerId: string, results: Result[]): PlayerRanking["recentFormLabel"] {
  if (results.length < 3) return "观察中";
  const recent = results.slice(-5);
  const topTwoCount = recent.filter((result) => {
    const entry = result.entries.find((item) => item.playerId === playerId);
    return entry ? entry.rank <= 2 : false;
  }).length;
  if (topTwoCount >= 4) return "手热";
  if (topTwoCount >= 2) return "稳定";
  return "回暖";
}

function getRecentScore(playerId: string, results: Result[]) {
  const recent = results.slice(-5);
  if (recent.length === 0) return 0;
  const score = recent.reduce((sum, result) => {
    const entry = result.entries.find((item) => item.playerId === playerId);
    if (!entry) return sum;
    return sum + (5 - entry.rank) / 4;
  }, 0);
  return score / recent.length;
}
```

- [ ] **Step 4: Run ranking tests**

Run:

```bash
cd mahjong-booking
npm test -- src/domain/rankings.test.ts
```

Expected: all tests PASS.

- [ ] **Step 5: Commit ranking logic**

Run:

```bash
git add mahjong-booking/src/domain/rankings.ts mahjong-booking/src/domain/rankings.test.ts
git commit -m "feat: calculate mahjong rankings"
```

Expected: commit succeeds.

## Task 4: Implement Session Transitions With Tests

**Files:**
- Create: `mahjong-booking/src/domain/sessions.ts`
- Create: `mahjong-booking/src/domain/sessions.test.ts`

- [ ] **Step 1: Write failing session tests**

Write `mahjong-booking/src/domain/sessions.test.ts`:

```ts
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
  noShowPlayerIds: []
};

describe("joinSession", () => {
  it("adds a player and marks the session ready when seats fill", () => {
    const next = joinSession(openSession, "d");
    expect(next.participantIds).toEqual(["a", "b", "c", "d"]);
    expect(next.status).toBe("ready");
  });

  it("adds extra players to the waitlist", () => {
    const full = { ...openSession, participantIds: ["a", "b", "c", "d"], status: "ready" as const };
    const next = joinSession(full, "e");
    expect(next.participantIds).toEqual(["a", "b", "c", "d"]);
    expect(next.waitlistIds).toEqual(["e"]);
  });
});

describe("cancelSeat", () => {
  it("promotes the first waitlisted player after cancellation", () => {
    const full = { ...openSession, participantIds: ["a", "b", "c", "d"], waitlistIds: ["e"], status: "ready" as const };
    const next = cancelSeat(full, "b");
    expect(next.participantIds).toEqual(["a", "c", "d", "e"]);
    expect(next.waitlistIds).toEqual([]);
    expect(next.status).toBe("ready");
  });
});
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
cd mahjong-booking
npm test -- src/domain/sessions.test.ts
```

Expected: FAIL because `./sessions` does not exist.

- [ ] **Step 3: Implement session helpers**

Write `mahjong-booking/src/domain/sessions.ts`:

```ts
import type { Session } from "../types";

export function joinSession(session: Session, playerId: string): Session {
  if (session.participantIds.includes(playerId) || session.waitlistIds.includes(playerId)) {
    return session;
  }

  if (session.participantIds.length < session.seatCount) {
    const participantIds = [...session.participantIds, playerId];
    return {
      ...session,
      participantIds,
      status: participantIds.length >= session.seatCount ? "ready" : "open"
    };
  }

  return {
    ...session,
    waitlistIds: [...session.waitlistIds, playerId]
  };
}

export function cancelSeat(session: Session, playerId: string): Session {
  if (session.waitlistIds.includes(playerId)) {
    return {
      ...session,
      waitlistIds: session.waitlistIds.filter((id) => id !== playerId)
    };
  }

  if (!session.participantIds.includes(playerId)) {
    return session;
  }

  const participantIds = session.participantIds.filter((id) => id !== playerId);
  const [promotedId, ...remainingWaitlistIds] = session.waitlistIds;
  const nextParticipantIds = promotedId ? [...participantIds, promotedId] : participantIds;

  return {
    ...session,
    participantIds: nextParticipantIds,
    waitlistIds: remainingWaitlistIds,
    status: nextParticipantIds.length >= session.seatCount ? "ready" : "open"
  };
}
```

- [ ] **Step 4: Run session tests**

Run:

```bash
cd mahjong-booking
npm test -- src/domain/sessions.test.ts
```

Expected: all tests PASS.

- [ ] **Step 5: Commit session logic**

Run:

```bash
git add mahjong-booking/src/domain/sessions.ts mahjong-booking/src/domain/sessions.test.ts
git commit -m "feat: manage mahjong session seats"
```

Expected: commit succeeds.

## Task 5: Build App State And Tab Navigation

**Files:**
- Modify: `mahjong-booking/src/App.tsx`
- Modify: `mahjong-booking/src/styles.css`

- [ ] **Step 1: Replace the shell with tab state**

Modify `mahjong-booking/src/App.tsx`:

```tsx
import { CalendarDays, ClipboardList, HomeIcon, Trophy, UserRound } from "lucide-react";
import { useMemo, useState } from "react";
import { players as seedPlayers, results as seedResults, sessions as seedSessions } from "./data/seed";
import { buildRankings } from "./domain/rankings";
import type { TabKey } from "./types";

const tabs: Array<{ key: TabKey; label: string; icon: typeof HomeIcon }> = [
  { key: "home", label: "首页", icon: HomeIcon },
  { key: "booking", label: "约局", icon: CalendarDays },
  { key: "results", label: "战绩", icon: ClipboardList },
  { key: "ranking", label: "排行", icon: Trophy },
  { key: "profile", label: "我的", icon: UserRound }
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("home");
  const [sessions] = useState(seedSessions);
  const [results] = useState(seedResults);
  const rankings = useMemo(() => buildRankings(seedPlayers, sessions, results, "all"), [sessions, results]);

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
        <section className="screen-body">
          <div className="empty-state">
            <h2>{activeTab}</h2>
            <p>排行榜第一名：{rankings[0]?.player.displayName ?? "暂无"}</p>
          </div>
        </section>
        <nav className="tab-bar" aria-label="主导航">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.key}
                className={activeTab === tab.key ? "tab-button active" : "tab-button"}
                type="button"
                onClick={() => setActiveTab(tab.key)}
              >
                <Icon size={18} strokeWidth={2.3} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </section>
    </main>
  );
}
```

- [ ] **Step 2: Add navigation styles**

Append to `mahjong-booking/src/styles.css`:

```css
.phone-frame {
  display: grid;
  grid-template-rows: auto 1fr auto;
}

.screen-body {
  min-height: 0;
  overflow: auto;
}

.tab-bar {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  border-top: 1px solid #29251f;
  background: #fffaf0;
}

.tab-button {
  min-height: 58px;
  border: 0;
  border-right: 1px solid rgba(41, 37, 31, 0.12);
  background: transparent;
  color: #776a5b;
  display: grid;
  place-items: center;
  gap: 3px;
  font-size: 11px;
  cursor: pointer;
}

.tab-button:last-child {
  border-right: 0;
}

.tab-button.active {
  background: #29251f;
  color: #fffaf0;
}
```

- [ ] **Step 3: Build and test**

Run:

```bash
cd mahjong-booking
npm test
npm run build
```

Expected: tests pass and production build succeeds.

- [ ] **Step 4: Commit navigation shell**

Run:

```bash
git add mahjong-booking/src/App.tsx mahjong-booking/src/styles.css
git commit -m "feat: add mahjong app navigation"
```

Expected: commit succeeds.

## Task 6: Build The Five Screens

**Files:**
- Create: `mahjong-booking/src/components/Home.tsx`
- Create: `mahjong-booking/src/components/Booking.tsx`
- Create: `mahjong-booking/src/components/Results.tsx`
- Create: `mahjong-booking/src/components/Ranking.tsx`
- Create: `mahjong-booking/src/components/Profile.tsx`
- Modify: `mahjong-booking/src/App.tsx`
- Modify: `mahjong-booking/src/styles.css`

- [ ] **Step 1: Create Home screen**

Write `mahjong-booking/src/components/Home.tsx`:

```tsx
import { Plus } from "lucide-react";
import type { Player, Session } from "../types";
import type { PlayerRanking } from "../domain/rankings";

interface HomeProps {
  players: Player[];
  sessions: Session[];
  rankings: PlayerRanking[];
}

export function Home({ players, sessions, rankings }: HomeProps) {
  const nextSession = sessions.find((session) => session.status === "open" || session.status === "ready");
  const leader = rankings.find((ranking) => ranking.eligibilityStatus === "official") ?? rankings[0];
  const playerMap = new Map(players.map((player) => [player.id, player]));

  return (
    <div className="screen-stack">
      <section className="hero-card">
        <div className="hero-meta">{nextSession?.startsAt.slice(5, 16).replace("T", " ") ?? "暂无约局"}</div>
        <h2>{nextSession ? `还差 ${Math.max(0, nextSession.seatCount - nextSession.participantIds.length)} 人开桌` : "发起今晚第一桌"}</h2>
        <p>{nextSession ? `${nextSession.location} · ${nextSession.note}` : "朋友局从一个时间和地点开始。"}</p>
        <div className="avatar-row">
          {nextSession?.participantIds.map((id) => {
            const player = playerMap.get(id);
            return <span key={id} className="avatar" style={{ background: player?.avatarColor }}>{player?.displayName.slice(0, 1)}</span>;
          })}
          {Array.from({ length: Math.max(0, (nextSession?.seatCount ?? 4) - (nextSession?.participantIds.length ?? 0)) }).map((_, index) => (
            <span key={index} className="avatar empty"><Plus size={15} /></span>
          ))}
        </div>
      </section>
      <section className="highlight-grid">
        <article className="metric-card green">
          <span>本周牌王</span>
          <strong>{leader?.player.displayName ?? "暂无"}</strong>
          <small>胜率 {Math.round((leader?.winRate ?? 0) * 100)}%</small>
        </article>
        <article className="metric-card gold">
          <span>最佳搭子</span>
          <strong>小林</strong>
          <small>出勤稳定</small>
        </article>
      </section>
      <section className="panel">
        <div className="panel-title"><strong>娱乐综合榜</strong><span>全部</span></div>
        {rankings.slice(0, 3).map((ranking, index) => (
          <div className="rank-row" key={ranking.player.id}>
            <b>{index + 1}</b>
            <span>{ranking.player.displayName}</span>
            <span>{Math.round(ranking.winRate * 100)}%</span>
            <em>{ranking.recentFormLabel}</em>
          </div>
        ))}
      </section>
    </div>
  );
}
```

- [ ] **Step 2: Create Booking screen**

Write `mahjong-booking/src/components/Booking.tsx`:

```tsx
import type { Player, Session } from "../types";

interface BookingProps {
  players: Player[];
  sessions: Session[];
  onJoin: (sessionId: string, playerId: string) => void;
  onCancel: (sessionId: string, playerId: string) => void;
}

export function Booking({ players, sessions, onJoin, onCancel }: BookingProps) {
  const player = players[4];

  return (
    <div className="screen-stack">
      <section className="form-card">
        <h2>发起约局</h2>
        <label>时间<input value="今晚 20:00" readOnly /></label>
        <label>地点<input value="老地方茶室" readOnly /></label>
        <label>备注<input value="三缺一，带点夜宵" readOnly /></label>
        <button type="button" className="primary-button">生成约局</button>
      </section>
      {sessions.map((session) => (
        <section className="panel session-card" key={session.id}>
          <div className="panel-title"><strong>{session.title}</strong><span>{session.status}</span></div>
          <p>{session.location} · {session.participantIds.length}/{session.seatCount}</p>
          <div className="button-row">
            <button type="button" className="primary-button" onClick={() => onJoin(session.id, player.id)}>安安报名</button>
            <button type="button" className="ghost-button" onClick={() => onCancel(session.id, player.id)}>取消</button>
          </div>
        </section>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: Create Results screen**

Write `mahjong-booking/src/components/Results.tsx`:

```tsx
import type { Player, Result, Session } from "../types";

interface ResultsProps {
  players: Player[];
  sessions: Session[];
  results: Result[];
}

export function Results({ players, sessions, results }: ResultsProps) {
  const playerMap = new Map(players.map((player) => [player.id, player]));

  return (
    <div className="screen-stack">
      <section className="form-card">
        <h2>录入整场结果</h2>
        <p>第一版按 1-4 名录入，参与者确认后刷新榜单。</p>
        {["第 1 名", "第 2 名", "第 3 名", "第 4 名"].map((label, index) => (
          <label key={label}>{label}<input value={players[index]?.displayName ?? ""} readOnly /></label>
        ))}
        <button type="button" className="primary-button">提交确认</button>
      </section>
      <section className="panel">
        <div className="panel-title"><strong>最近战绩</strong><span>已确认</span></div>
        {results.map((result) => {
          const session = sessions.find((item) => item.id === result.sessionId);
          const winner = result.entries.find((entry) => entry.rank === 1);
          return (
            <div className="rank-row" key={result.id}>
              <b>赢</b>
              <span>{session?.title}</span>
              <span>{winner ? playerMap.get(winner.playerId)?.displayName : "暂无"}</span>
              <em>{result.status === "confirmed" ? "确认" : "待确认"}</em>
            </div>
          );
        })}
      </section>
    </div>
  );
}
```

- [ ] **Step 4: Create Ranking screen**

Write `mahjong-booking/src/components/Ranking.tsx`:

```tsx
import type { PlayerRanking } from "../domain/rankings";

interface RankingProps {
  rankings: PlayerRanking[];
}

export function Ranking({ rankings }: RankingProps) {
  const official = rankings.filter((ranking) => ranking.eligibilityStatus === "official");
  const observation = rankings.filter((ranking) => ranking.eligibilityStatus === "observation");

  return (
    <div className="screen-stack">
      <section className="segmented">
        <button className="active" type="button">全部</button>
        <button type="button">本月</button>
        <button type="button">本周</button>
      </section>
      <section className="panel">
        <div className="panel-title"><strong>正式排名</strong><span>满 3 场</span></div>
        {official.map((ranking) => (
          <div className="rank-row large" key={ranking.player.id}>
            <b>{ranking.rank}</b>
            <span>{ranking.player.displayName}</span>
            <span>{ranking.comprehensiveScore}</span>
            <em>{Math.round(ranking.winRate * 100)}%</em>
          </div>
        ))}
      </section>
      <section className="panel">
        <div className="panel-title"><strong>观察席</strong><span>未满 3 场</span></div>
        {observation.map((ranking) => (
          <div className="rank-row" key={ranking.player.id}>
            <b>观</b>
            <span>{ranking.player.displayName}</span>
            <span>{ranking.completedSessionCount} 场</span>
            <em>{ranking.recentFormLabel}</em>
          </div>
        ))}
      </section>
    </div>
  );
}
```

- [ ] **Step 5: Create Profile screen**

Write `mahjong-booking/src/components/Profile.tsx`:

```tsx
import type { PlayerRanking } from "../domain/rankings";

interface ProfileProps {
  ranking: PlayerRanking;
}

export function Profile({ ranking }: ProfileProps) {
  return (
    <div className="screen-stack">
      <section className="profile-card">
        <span className="avatar xl" style={{ background: ranking.player.avatarColor }}>{ranking.player.displayName.slice(0, 1)}</span>
        <h2>{ranking.player.displayName}</h2>
        <p>{ranking.eligibilityStatus === "official" ? `综合第 ${ranking.rank} 名` : "观察席成员"}</p>
      </section>
      <section className="stats-grid">
        <div><strong>{Math.round(ranking.winRate * 100)}%</strong><span>胜率</span></div>
        <div><strong>{ranking.completedSessionCount}</strong><span>场次</span></div>
        <div><strong>{ranking.currentStreak}</strong><span>连胜</span></div>
        <div><strong>{ranking.noShowCount}</strong><span>爽约</span></div>
      </section>
      <section className="panel">
        <div className="panel-title"><strong>最近状态</strong><span>{ranking.recentFormLabel}</span></div>
        <p className="muted">常用搭子：小林、老周。确认战绩后这里会更新最近牌局。</p>
      </section>
    </div>
  );
}
```

- [ ] **Step 6: Wire screens into App state**

Modify `mahjong-booking/src/App.tsx`:

```tsx
import { CalendarDays, ClipboardList, HomeIcon, Trophy, UserRound } from "lucide-react";
import { useMemo, useState } from "react";
import { Booking } from "./components/Booking";
import { Home } from "./components/Home";
import { Profile } from "./components/Profile";
import { Ranking } from "./components/Ranking";
import { Results } from "./components/Results";
import { players as seedPlayers, results as seedResults, sessions as seedSessions } from "./data/seed";
import { buildRankings } from "./domain/rankings";
import { cancelSeat, joinSession } from "./domain/sessions";
import type { Session, TabKey } from "./types";

const tabs: Array<{ key: TabKey; label: string; icon: typeof HomeIcon }> = [
  { key: "home", label: "首页", icon: HomeIcon },
  { key: "booking", label: "约局", icon: CalendarDays },
  { key: "results", label: "战绩", icon: ClipboardList },
  { key: "ranking", label: "排行", icon: Trophy },
  { key: "profile", label: "我的", icon: UserRound }
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("home");
  const [sessions, setSessions] = useState<Session[]>(seedSessions);
  const [results] = useState(seedResults);
  const rankings = useMemo(() => buildRankings(seedPlayers, sessions, results, "all"), [sessions, results]);

  function updateSession(sessionId: string, updater: (session: Session) => Session) {
    setSessions((current) => current.map((session) => (session.id === sessionId ? updater(session) : session)));
  }

  const screen = {
    home: <Home players={seedPlayers} sessions={sessions} rankings={rankings} />,
    booking: (
      <Booking
        players={seedPlayers}
        sessions={sessions}
        onJoin={(sessionId, playerId) => updateSession(sessionId, (session) => joinSession(session, playerId))}
        onCancel={(sessionId, playerId) => updateSession(sessionId, (session) => cancelSeat(session, playerId))}
      />
    ),
    results: <Results players={seedPlayers} sessions={sessions} results={results} />,
    ranking: <Ranking rankings={rankings} />,
    profile: <Profile ranking={rankings.find((ranking) => ranking.player.id === "ajie") ?? rankings[0]} />
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
            const Icon = tab.icon;
            return (
              <button
                key={tab.key}
                className={activeTab === tab.key ? "tab-button active" : "tab-button"}
                type="button"
                onClick={() => setActiveTab(tab.key)}
              >
                <Icon size={18} strokeWidth={2.3} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </section>
    </main>
  );
}
```

- [ ] **Step 7: Add screen styles**

Append to `mahjong-booking/src/styles.css`:

```css
.screen-stack {
  display: grid;
  gap: 14px;
  padding: 16px;
}

.hero-card,
.panel,
.form-card,
.profile-card {
  border: 1px solid #29251f;
  background: #fffaf0;
  padding: 16px;
}

.hero-card {
  background: #fffaf0;
}

.hero-meta,
.muted {
  color: #776a5b;
  font-size: 13px;
}

.hero-card h2,
.form-card h2,
.profile-card h2 {
  margin: 6px 0;
  font-size: 28px;
  line-height: 1.12;
  font-family: Georgia, "Times New Roman", serif;
}

.avatar-row {
  display: flex;
  gap: 8px;
  margin-top: 15px;
}

.avatar {
  width: 40px;
  height: 40px;
  border: 1px solid #29251f;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 700;
}

.avatar.empty {
  background: #fffaf0;
  color: #776a5b;
  border-style: dashed;
}

.avatar.xl {
  width: 72px;
  height: 72px;
  font-size: 30px;
  margin: 0 auto 10px;
}

.highlight-grid,
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.metric-card,
.stats-grid div {
  border: 1px solid #29251f;
  padding: 14px;
}

.metric-card {
  display: grid;
  gap: 5px;
}

.metric-card.green {
  background: #1f6650;
  color: #fff;
}

.metric-card.gold {
  background: #e7b84b;
}

.metric-card strong,
.stats-grid strong {
  font-size: 24px;
}

.panel-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.panel-title span {
  color: #776a5b;
  font-size: 12px;
}

.rank-row {
  display: grid;
  grid-template-columns: 34px 1fr 54px 52px;
  gap: 8px;
  align-items: center;
  min-height: 38px;
  border-top: 1px solid rgba(41, 37, 31, 0.12);
  font-size: 13px;
}

.rank-row:first-of-type {
  border-top: 0;
}

.rank-row.large {
  min-height: 48px;
  font-size: 15px;
}

.rank-row em {
  font-style: normal;
  color: #1f6650;
}

.form-card {
  display: grid;
  gap: 10px;
}

.form-card label {
  display: grid;
  gap: 5px;
  color: #776a5b;
  font-size: 12px;
}

.form-card input {
  height: 40px;
  border: 1px solid rgba(41, 37, 31, 0.25);
  background: #fff;
  padding: 0 10px;
  color: #29251f;
}

.button-row {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.primary-button,
.ghost-button {
  min-height: 40px;
  border: 1px solid #29251f;
  padding: 0 12px;
  cursor: pointer;
}

.primary-button {
  background: #dc3f2f;
  color: #fff;
}

.ghost-button {
  background: #fffaf0;
  color: #29251f;
}

.segmented {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border: 1px solid #29251f;
}

.segmented button {
  border: 0;
  border-right: 1px solid #29251f;
  min-height: 38px;
  background: #fffaf0;
}

.segmented button:last-child {
  border-right: 0;
}

.segmented button.active {
  background: #29251f;
  color: #fffaf0;
}

.profile-card {
  text-align: center;
}

@media (max-width: 460px) {
  .app-shell {
    padding: 0;
  }

  .phone-frame {
    min-height: 100vh;
    width: 100%;
    border: 0;
  }
}
```

- [ ] **Step 8: Build and test**

Run:

```bash
cd mahjong-booking
npm test
npm run build
```

Expected: tests pass and build succeeds.

- [ ] **Step 9: Commit the screens**

Run:

```bash
git add mahjong-booking/src
git commit -m "feat: build mahjong miniapp screens"
```

Expected: commit succeeds.

## Task 7: Visual Verification And Polish

**Files:**
- Modify: `mahjong-booking/src/styles.css`
- Modify: React component files only if screenshot review reveals overflow or unclear hierarchy.

- [ ] **Step 1: Start the dev server**

Run:

```bash
cd mahjong-booking
npm run dev
```

Expected: Vite serves the app at `http://127.0.0.1:5178/`.

- [ ] **Step 2: Inspect desktop mobile-frame viewport**

Open `http://127.0.0.1:5178/` in the browser at `1280x900`.

Expected: centered phone frame, no blank screen, clear top bar, visible bottom navigation, and Home content fits without overlapping.

- [ ] **Step 3: Inspect narrow mobile viewport**

Open `http://127.0.0.1:5178/` at `390x844`.

Expected: app fills the viewport, tab labels fit, hero title wraps cleanly, rank rows do not overflow horizontally.

- [ ] **Step 4: Click through all tabs**

Click Home, Booking, Results, Ranking, and Profile.

Expected:

- Home shows next session and top three ranking rows.
- Booking shows session cards and the `安安报名` interaction updates the current open session from `3/4` to `4/4`.
- Results shows the rank-entry form and recent confirmed results.
- Ranking shows official rankings and observation players separately.
- Profile shows 阿杰's stats.

- [ ] **Step 5: Apply visual fixes found during inspection**

If text overflow appears in rank rows, update `.rank-row` in `mahjong-booking/src/styles.css`:

```css
.rank-row {
  grid-template-columns: 30px minmax(0, 1fr) 48px 48px;
}

.rank-row span,
.rank-row em {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

If the phone frame is too tall on desktop, update `.phone-frame`:

```css
.phone-frame {
  max-height: min(860px, calc(100vh - 48px));
}
```

- [ ] **Step 6: Run final verification**

Run:

```bash
cd mahjong-booking
npm test
npm run build
```

Expected: tests pass and build succeeds.

- [ ] **Step 7: Commit visual polish**

Run:

```bash
git add mahjong-booking
git commit -m "polish: refine mahjong miniapp prototype"
```

Expected: commit succeeds if there were visual or interaction changes. If Step 5 made no changes, skip this commit.

## Self-Review

- Spec coverage: The plan covers session creation UI, join/cancel/waitlist state, result entry display, ranking calculations, eligibility threshold, profile stats, visual direction, and mobile verification.
- Scope: The plan intentionally excludes venue inventory, payments, chat, detailed scoring, tournament brackets, and public game discovery.
- Type consistency: `Session`, `Result`, `Player`, `RankingPeriod`, `TabKey`, `PlayerRanking`, `joinSession`, `cancelSeat`, and `buildRankings` are introduced before use and keep consistent names.
- Placeholder scan: The plan contains no unfinished markers, and every implementation reference is introduced before use.
