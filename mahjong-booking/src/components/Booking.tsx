import { useState } from "react";

import type { Player, Session } from "../types";

export interface CreateSessionDraft {
  startsAt: string;
  location: string;
  seatCount: number;
  note: string;
}

interface BookingProps {
  players: Player[];
  sessions: Session[];
  currentPlayer?: Player;
  onJoin: (sessionId: string, playerId: string) => void;
  onCancel: (sessionId: string, playerId: string) => void;
  onCreate: (draft: CreateSessionDraft) => void;
}

export function Booking({ currentPlayer, players, sessions, onCreate, onJoin, onCancel }: BookingProps) {
  const player = currentPlayer ?? players[4];
  const [startsAt, setStartsAt] = useState("2026-07-24T20:00:00+08:00");
  const [location, setLocation] = useState("老地方茶室");
  const [seatCount, setSeatCount] = useState(4);
  const [note, setNote] = useState("三缺一，带点夜宵");

  return (
    <div className="screen-stack">
      <section className="form-card">
        <h2>发起约局</h2>
        <label>
          时间
          <input value={startsAt} onChange={(event) => setStartsAt(event.target.value)} />
        </label>
        <label>
          地点
          <input value={location} onChange={(event) => setLocation(event.target.value)} />
        </label>
        <label>
          人数
          <input
            min={2}
            max={4}
            type="number"
            value={seatCount}
            onChange={(event) => setSeatCount(Number(event.target.value))}
          />
        </label>
        <label>
          备注
          <input value={note} onChange={(event) => setNote(event.target.value)} />
        </label>
        <button
          type="button"
          className="primary-button"
          disabled={!startsAt.trim() || !location.trim() || seatCount < 2}
          onClick={() =>
            onCreate({
              startsAt: startsAt.trim(),
              location: location.trim(),
              seatCount: Math.min(4, Math.max(2, seatCount)),
              note: note.trim(),
            })
          }
        >
          生成约局
        </button>
      </section>
      {sessions.map((session) => (
        <section className="panel session-card" key={session.id}>
          {(() => {
            const isBookable = session.status === "open" || session.status === "ready";
            const isCurrentParticipant = player ? session.participantIds.includes(player.id) : false;
            const isCurrentWaitlisted = player ? session.waitlistIds.includes(player.id) : false;
            const isFull = session.participantIds.length >= session.seatCount;
            const joinLabel = isCurrentParticipant
              ? "已报名"
              : isCurrentWaitlisted
                ? "候补中"
                : isFull
                  ? "加入候补"
                  : `${player?.displayName ?? ""}报名`;

            return (
              <>
          <div className="panel-title">
            <strong>{session.title}</strong>
            <span>{getSessionStatusLabel(session)}</span>
          </div>
          <p>
            {session.location} · {session.participantIds.length}/{session.seatCount}
          </p>
          {isBookable ? (
            <div className="button-row">
              <button
                type="button"
                className="primary-button"
                disabled={!player || isCurrentParticipant || isCurrentWaitlisted}
                onClick={() => {
                  if (player) {
                    onJoin(session.id, player.id);
                  }
                }}
              >
                {player ? joinLabel : "报名"}
              </button>
              <button
                type="button"
                className="ghost-button"
                disabled={!player || (!isCurrentParticipant && !isCurrentWaitlisted)}
                onClick={() => {
                  if (player) {
                    onCancel(session.id, player.id);
                  }
                }}
              >
                取消
              </button>
            </div>
          ) : (
            <p className="muted session-state">已结束 · 不可修改</p>
          )}
          {!player ? <p className="muted session-state">未选择成员，暂不可报名</p> : null}
              </>
            );
          })()}
        </section>
      ))}
    </div>
  );
}

function getSessionStatusLabel(session: Session): string {
  if (session.status === "open") {
    return "可报名";
  }

  if (session.status === "ready") {
    return "已满员";
  }

  return "已结束";
}
