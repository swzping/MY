import { useMemo, useState } from 'react';
import { BrainCircuit, Network, RefreshCw, Search } from 'lucide-react';
import rawData from './data/study-data.json';
import { CategoryFilter } from './components/CategoryFilter';
import { StudyHighlights } from './components/StudyHighlights';
import { TagCloud } from './components/TagCloud';
import type { StudyData, StudyTag, StudyTagCategory } from './types';

const data = rawData as StudyData;
const defaultTag = data.tags.find((tag) => tag.name === 'MCP') ?? data.tags[0];

export default function App() {
  const [activeCategory, setActiveCategory] = useState<StudyTagCategory | 'all'>('all');
  const [selectedTag, setSelectedTag] = useState<StudyTag>(defaultTag);

  const counts = useMemo(() => {
    return data.tags.reduce(
      (acc, tag) => {
        acc[tag.category] += 1;
        return acc;
      },
      { term: 0, agent: 0, resource: 0, project: 0, trend: 0, action: 0 } as Record<StudyTagCategory, number>,
    );
  }, []);

  const visibleTags = activeCategory === 'all' ? data.tags : data.tags.filter((tag) => tag.category === activeCategory);

  return (
    <main className="app-shell">
      <section className="hero-band">
        <div className="hero-copy">
          <span className="eyebrow">Personal Knowledge Atlas</span>
          <h1>Study 学习知识星图</h1>
          <p>把 Markdown 笔记同步成可筛选的标签云，用悬停简介快速回忆概念、Agent、收藏资源和项目案例。</p>
          <div className="hero-actions">
            <span><Network size={16} /> {data.tags.length} 个标签</span>
            <span><BrainCircuit size={16} /> {data.documents.length} 篇笔记</span>
            <span><RefreshCw size={16} /> npm run generate:study</span>
          </div>
        </div>
        <div className="search-shell" aria-label="视觉搜索框">
          <Search size={18} />
          <span>点击分类或悬停标签查看简介</span>
        </div>
      </section>

      <CategoryFilter activeCategory={activeCategory} counts={counts} onChange={setActiveCategory} />

      <section className="workspace-grid">
        <TagCloud tags={visibleTags} selectedTagName={selectedTag.name} onSelectTag={setSelectedTag} />
        <StudyHighlights data={data} selectedTag={selectedTag} />
      </section>
    </main>
  );
}
