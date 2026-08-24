import type { StudyTagCategory } from '../types';

interface CategoryFilterProps {
  activeCategory: StudyTagCategory | 'all';
  counts: Record<StudyTagCategory, number>;
  onChange: (category: StudyTagCategory | 'all') => void;
}

const labels: Record<StudyTagCategory | 'all', string> = {
  all: '全部',
  term: '术语',
  agent: 'Agent',
  resource: '收藏',
  project: '项目',
  trend: '趋势',
  action: '行动',
};

export function CategoryFilter({ activeCategory, counts, onChange }: CategoryFilterProps) {
  const categories = Object.keys(labels) as Array<StudyTagCategory | 'all'>;

  return (
    <div className="category-filter" aria-label="标签分类筛选">
      {categories.map((category) => (
        <button
          key={category}
          type="button"
          className={activeCategory === category ? 'category-pill active' : 'category-pill'}
          onClick={() => onChange(category)}
        >
          <span>{labels[category]}</span>
          <strong>{category === 'all' ? Object.values(counts).reduce((sum, count) => sum + count, 0) : counts[category]}</strong>
        </button>
      ))}
    </div>
  );
}
