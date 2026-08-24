import type { PlayerRanking } from "../domain/rankings";
import type { RankingPeriod } from "../types";

interface RankingProps {
  period: RankingPeriod;
  rankings: PlayerRanking[];
  onPeriodChange: (period: RankingPeriod) => void;
}

const periods: Array<{ key: RankingPeriod; label: string }> = [
  { key: "all", label: "全部" },
  { key: "month", label: "本月" },
  { key: "week", label: "本周" },
];

export function Ranking({ onPeriodChange, period, rankings }: RankingProps) {
  const official = rankings.filter((ranking) => ranking.eligibilityStatus === "official");
  const observation = rankings.filter((ranking) => ranking.eligibilityStatus === "observation");

  return (
    <div className="screen-stack">
      <section className="segmented" aria-label="排行榜周期">
        {periods.map((item) => (
          <button
            key={item.key}
            className={period === item.key ? "active" : undefined}
            type="button"
            onClick={() => onPeriodChange(item.key)}
          >
            {item.label}
          </button>
        ))}
      </section>
      <section className="panel">
        <div className="panel-title">
          <strong>正式排名</strong>
          <span>满 3 场</span>
        </div>
        {official.length > 0 ? (
          official.map((ranking) => (
            <div className="rank-row large" key={ranking.player.id}>
              <b>{ranking.rank}</b>
              <span>{ranking.player.displayName}</span>
              <span>{ranking.comprehensiveScore}</span>
              <em>{Math.round(ranking.winRate * 100)}%</em>
            </div>
          ))
        ) : (
          <p className="muted">暂无正式排名</p>
        )}
      </section>
      <section className="panel">
        <div className="panel-title">
          <strong>观察席</strong>
          <span>未满 3 场</span>
        </div>
        {observation.length > 0 ? (
          observation.map((ranking) => (
            <div className="rank-row" key={ranking.player.id}>
              <b>观</b>
              <span>{ranking.player.displayName}</span>
              <span>{ranking.completedSessionCount} 场</span>
              <em>{ranking.recentFormLabel}</em>
            </div>
          ))
        ) : (
          <p className="muted">暂无观察成员</p>
        )}
      </section>
    </div>
  );
}
