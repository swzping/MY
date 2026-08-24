import type { StudyData, StudyTag } from '../types';

interface StudyHighlightsProps {
  data: StudyData;
  selectedTag: StudyTag;
}

export function StudyHighlights({ data, selectedTag }: StudyHighlightsProps) {
  const sourceDocs = data.documents.filter((doc) => selectedTag.sources.includes(doc.path));
  const recentDocs = data.documents.slice(0, 5);

  return (
    <aside className="study-highlights" aria-label="标签详情">
      <div className="detail-card featured">
        <span className="eyebrow">当前标签</span>
        <h2>{selectedTag.name}</h2>
        <p>{selectedTag.description}</p>
        <div className="related-row">
          {selectedTag.related.slice(0, 6).map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      </div>

      <div className="detail-card">
        <span className="eyebrow">来源笔记</span>
        {sourceDocs.map((doc) => (
          <div key={doc.path} className="source-line">
            <strong>{doc.title}</strong>
            <span>{doc.path}</span>
          </div>
        ))}
      </div>

      <div className="detail-card">
        <span className="eyebrow">阅读路径</span>
        {recentDocs.map((doc) => (
          <div key={doc.path} className="source-line compact">
            <strong>{doc.title}</strong>
            <span>{doc.summary}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}
