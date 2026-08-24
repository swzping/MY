import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { players, results, sessions } from "../data/seed";
import type { PlayerRanking } from "../domain/rankings";
import { Booking } from "./Booking";
import { Profile } from "./Profile";
import { Ranking } from "./Ranking";
import { Results } from "./Results";

const noopCreate = vi.fn();

describe("screen guards", () => {
  it("does not expose booking actions for completed historical sessions", () => {
    const markup = renderToStaticMarkup(
      <Booking players={players} sessions={[sessions[1]]} onCreate={noopCreate} onJoin={vi.fn()} onCancel={vi.fn()} />,
    );

    expect(markup).toContain("已结束");
    expect(markup).not.toContain("安安报名");
    expect(markup).not.toContain("取消");
  });

  it("shows a visible booking fallback when the current player is missing", () => {
    const markup = renderToStaticMarkup(
      <Booking players={[]} sessions={[sessions[0]]} onCreate={noopCreate} onJoin={vi.fn()} onCancel={vi.fn()} />,
    );

    expect(markup).toContain("未选择成员");
    expect(markup).toContain("disabled");
  });

  it("shows an already-joined state for the current player", () => {
    const markup = renderToStaticMarkup(
      <Booking
        currentPlayer={players[0]}
        players={players}
        sessions={[sessions[0]]}
        onCreate={noopCreate}
        onJoin={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(markup).toContain("已报名");
    expect(markup).toContain("disabled");
  });

  it("shows a waitlist action when an unjoined player sees a full ready session", () => {
    const markup = renderToStaticMarkup(
      <Booking
        currentPlayer={players[5]}
        players={players}
        sessions={[{ ...sessions[0], status: "ready", participantIds: ["ajie", "xiaolin", "laozhou", "anan"] }]}
        onCreate={noopCreate}
        onJoin={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(markup).toContain("加入候补");
  });

  it("renders profile empty state when ranking is missing", () => {
    const markup = renderToStaticMarkup(<Profile />);

    expect(markup).toContain("暂无个人数据");
  });

  it("renders unknown player for a missing result winner lookup", () => {
    const markup = renderToStaticMarkup(
      <Results players={[]} sessions={sessions} results={[results[0]]} onSubmitResult={vi.fn()} />,
    );

    expect(markup).toContain("未知玩家");
  });

  it("does not allow result submission for an open incomplete session", () => {
    const markup = renderToStaticMarkup(
      <Results currentPlayer={players[0]} players={players} sessions={[sessions[0]]} results={[]} onSubmitResult={vi.fn()} />,
    );

    expect(markup).toContain("暂无满员待结算牌局");
    expect(markup).toContain("disabled");
  });

  it("restricts result options to ready-session participants", () => {
    const markup = renderToStaticMarkup(
      <Results
        currentPlayer={players[0]}
        players={players}
        sessions={[{ ...sessions[0], status: "ready", participantIds: ["ajie", "xiaolin", "laozhou", "anan"] }]}
        results={[]}
        onSubmitResult={vi.fn()}
      />,
    );

    expect(markup).toContain("阿杰");
    expect(markup).toContain("安安");
    expect(markup).not.toContain("大力");
  });

  it("renders ranking empty states", () => {
    const markup = renderToStaticMarkup(
      <Ranking period="all" rankings={[] as PlayerRanking[]} onPeriodChange={vi.fn()} />,
    );

    expect(markup).toContain("暂无正式排名");
    expect(markup).toContain("暂无观察成员");
  });
});
