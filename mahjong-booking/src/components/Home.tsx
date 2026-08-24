import { Plus } from "lucide-react";

import type { PlayerRanking } from "../domain/rankings";
import type { Player, Session } from "../types";

interface HomeProps {
  currentPlayer?: Player;
  players: Player[];
  sessions: Session[];
  rankings: PlayerRanking[];
  onJoin: (sessionId: string, playerId: string) => void;
}

export function Home({ currentPlayer, onJoin, players, sessions, rankings }: HomeProps) {
  const nextSession = sessions.find((session) => session.status === "open" || session.status === "ready");
  const leader = rankings.find((ranking) => ranking.eligibilityStatus === "official") ?? rankings[0];
  const playerMap = new Map(players.map((player) => [player.id, player]));
  const emptySeatCount = Math.max(0, (nextSession?.seatCount ?? 4) - (nextSession?.participantIds.length ?? 0));
  const isCurrentParticipant = Boolean(currentPlayer && nextSession?.participantIds.includes(currentPlayer.id));
  const isCurrentWaitlisted = Boolean(currentPlayer && nextSession?.waitlistIds.includes(currentPlayer.id));
  const joinLabel = isCurrentParticipant ? "已报名" : isCurrentWaitlisted ? "候补中" : emptySeatCount === 0 ? "加入候补" : "我要报名";

  return (
    <div className="screen-stack">
      <section className="hero-card">
        <div className="hero-meta">{nextSession?.startsAt.slice(5, 16).replace("T", " ") ?? "暂无约局"}</div>
        <h2>{nextSession ? `还差 ${emptySeatCount} 人开桌` : "发起今晚第一桌"}</h2>
        <p>{nextSession ? `${nextSession.location} · ${nextSession.note}` : "朋友局从一个时间和地点开始。"}</p>
        <div className="avatar-row" aria-label="已报名成员">
          {nextSession?.participantIds.map((id) => {
            const player = playerMap.get(id);

            return (
              <span key={id} className="avatar" style={{ background: player?.avatarColor }} title={player?.displayName}>
                {player?.displayName.slice(0, 1)}
              </span>
            );
          })}
          {Array.from({ length: emptySeatCount }).map((_, index) => (
            <span key={index} className="avatar empty" title="空位">
              <Plus aria-hidden="true" size={15} />
            </span>
          ))}
        </div>
        {nextSession ? (
          <div className="hero-actions">
            <button
              type="button"
              className="primary-button"
              disabled={!currentPlayer || isCurrentParticipant || isCurrentWaitlisted}
              onClick={() => {
                if (currentPlayer) {
                  onJoin(nextSession.id, currentPlayer.id);
                }
              }}
            >
              {joinLabel}
            </button>
          </div>
        ) : null}
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
        <div className="panel-title">
          <strong>娱乐综合榜</strong>
          <span>全部</span>
        </div>
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
