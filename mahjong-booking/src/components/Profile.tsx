import type { PlayerRanking } from "../domain/rankings";

interface ProfileProps {
  ranking?: PlayerRanking;
}

export function Profile({ ranking }: ProfileProps) {
  if (!ranking) {
    return (
      <div className="screen-stack">
        <section className="profile-card">
          <h2>暂无个人数据</h2>
          <p>完成一场牌局后，这里会显示你的胜率、场次和最近状态。</p>
        </section>
      </div>
    );
  }

  return (
    <div className="screen-stack">
      <section className="profile-card">
        <span className="avatar xl" style={{ background: ranking.player.avatarColor }}>
          {ranking.player.displayName.slice(0, 1)}
        </span>
        <h2>{ranking.player.displayName}</h2>
        <p>{ranking.eligibilityStatus === "official" ? `综合第 ${ranking.rank} 名` : "观察席成员"}</p>
      </section>
      <section className="stats-grid">
        <div>
          <strong>{Math.round(ranking.winRate * 100)}%</strong>
          <span>胜率</span>
        </div>
        <div>
          <strong>{ranking.completedSessionCount}</strong>
          <span>场次</span>
        </div>
        <div>
          <strong>{ranking.currentStreak}</strong>
          <span>连胜</span>
        </div>
        <div>
          <strong>{ranking.noShowCount}</strong>
          <span>爽约</span>
        </div>
      </section>
      <section className="panel">
        <div className="panel-title">
          <strong>最近状态</strong>
          <span>{ranking.recentFormLabel}</span>
        </div>
        <p className="muted">常用搭子：小林、老周。确认战绩后这里会更新最近牌局。</p>
      </section>
    </div>
  );
}
