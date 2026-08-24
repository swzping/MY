import type { CSSProperties } from 'react';
import type { StudyTag, StudyTagCategory } from '../types';
import { TagTooltip } from './TagTooltip';

interface TagCloudProps {
  tags: StudyTag[];
  selectedTagName: string;
  onSelectTag: (tag: StudyTag) => void;
}

const categoryNames: Record<StudyTagCategory, string> = {
  term: '概念名词术语',
  agent: 'Agent 工具平台',
  resource: '收藏地址资源',
  project: '项目案例模板',
  trend: '新闻趋势',
  action: '学习行动',
};

const orderedCategories: StudyTagCategory[] = ['term', 'agent', 'resource', 'project', 'trend', 'action'];

export function TagCloud({ tags, selectedTagName, onSelectTag }: TagCloudProps) {
  const groups = groupByCategory(tags);

  return (
    <section className="tag-cloud-panel" aria-label="知识标签云">
      {orderedCategories
        .filter((category) => groups[category].length > 0)
        .map((category) => (
          <div key={category} className={`tag-cluster cluster-${category}`}>
            <div className="cluster-heading">
              <span>{categoryNames[category]}</span>
              <strong>{groups[category].length}</strong>
            </div>
            <div className="tag-orbit">
              {groups[category].map((tag) => (
                <button
                  key={`${tag.category}-${tag.name}`}
                  type="button"
                  className={selectedTagName === tag.name ? 'tag-token selected' : 'tag-token'}
                  style={{ '--weight': Math.min(tag.weight, 10) } as CSSProperties}
                  onClick={() => onSelectTag(tag)}
                >
                  <span>{tag.name}</span>
                  <TagTooltip tag={tag} />
                </button>
              ))}
            </div>
          </div>
        ))}
    </section>
  );
}

function groupByCategory(tags: StudyTag[]): Record<StudyTagCategory, StudyTag[]> {
  return tags.reduce(
    (groups, tag) => {
      groups[tag.category].push(tag);
      return groups;
    },
    { term: [], agent: [], resource: [], project: [], trend: [], action: [] } as Record<StudyTagCategory, StudyTag[]>,
  );
}
