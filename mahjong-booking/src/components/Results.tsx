import { useMemo, useState } from "react";

import type { Player, Result, Session } from "../types";

interface ResultsProps {
  players: Player[];
  sessions: Session[];
  results: Result[];
  currentPlayer?: Player;
  onSubmitResult: (sessionId: string, orderedPlayerIds: string[]) => void;
}

export function Results({ currentPlayer, players, sessions, results, onSubmitResult }: ResultsProps) {
  const playerMap = new Map(players.map((player) => [player.id, player]));
  const resultSession = sessions.find((session) => session.status === "ready");
  const candidates = useMemo(() => {
    const participantIds = resultSession?.participantIds ?? [];
    return participantIds.slice(0, resultSession?.seatCount ?? 4);
  }, [resultSession]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const orderedPlayerIds = [0, 1, 2, 3].map((index) => selectedIds[index] || candidates[index] || "");
  const canSubmit =
    Boolean(currentPlayer && resultSession) &&
    orderedPlayerIds.length === (resultSession?.seatCount ?? 0) &&
    orderedPlayerIds.every(Boolean) &&
    new Set(orderedPlayerIds).size === orderedPlayerIds.length;

  return (
    <div className="screen-stack">
      <section className="form-card">
        <h2>录入整场结果</h2>
        <p>{resultSession ? `${resultSession.title} · 按参与者名次录入，提交后刷新榜单。` : "暂无满员待结算牌局。"}</p>
        {["第 1 名", "第 2 名", "第 3 名", "第 4 名"].slice(0, resultSession?.seatCount ?? 4).map((label, index) => (
          <label key={label}>
            {label}
            <select
              value={orderedPlayerIds[index]}
              disabled={!resultSession}
              onChange={(event) => {
                const next = [...selectedIds];
                next[index] = event.target.value;
                setSelectedIds(next);
              }}
            >
              {candidates.map((playerId) => (
                <option key={playerId} value={playerId}>
                  {playerMap.get(playerId)?.displayName ?? "未知玩家"}
                </option>
              ))}
            </select>
          </label>
        ))}
        <button
          type="button"
          className="primary-button"
          disabled={!canSubmit}
          onClick={() => {
            if (resultSession) {
              onSubmitResult(resultSession.id, orderedPlayerIds);
            }
          }}
        >
          提交确认
        </button>
      </section>
      <section className="panel">
        <div className="panel-title">
          <strong>最近战绩</strong>
          <span>已确认</span>
        </div>
        {results.map((result) => {
          const session = sessions.find((item) => item.id === result.sessionId);
          const winner = result.entries.find((entry) => entry.rank === 1);

          return (
            <div className="rank-row" key={result.id}>
              <b>赢</b>
              <span>{session?.title ?? "未知牌局"}</span>
              <span>{winner ? (playerMap.get(winner.playerId)?.displayName ?? "未知玩家") : "暂无"}</span>
              <em>{result.status === "confirmed" ? "确认" : "待确认"}</em>
            </div>
          );
        })}
      </section>
    </div>
  );
}
