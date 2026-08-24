import type { StudyTag, StudyTagCategory } from '../types';

interface TagTooltipProps {
  tag: StudyTag;
}

const categoryNames: Record<StudyTagCategory, string> = {
  term: '概念 / 名词 / 术语',
  agent: 'Agent / 工具 / 平台',
  resource: '收藏地址 / 人物 / 资源',
  project: '项目 / 案例 / 模板',
  trend: '新闻趋势',
  action: '学习行动',
};

export function TagTooltip({ tag }: TagTooltipProps) {
  return (
    <span className="tag-tooltip" role="tooltip">
      <span className="tooltip-category">{categoryNames[tag.category]}</span>
      <strong>{tag.name}</strong>
      <span>{tag.description}</span>
      <span className="tooltip-source">来源：{tag.sources.slice(0, 2).join('、')}</span>
      {tag.related.length > 0 ? <span className="tooltip-source">相关：{tag.related.slice(0, 4).join(' / ')}</span> : null}
    </span>
  );
}
