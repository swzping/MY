export type StudyTagCategory = 'term' | 'agent' | 'resource' | 'project' | 'trend' | 'action';

export interface StudyDocument {
  path: string;
  title: string;
  summary: string;
  category: StudyTagCategory;
}

export interface StudyTag {
  name: string;
  category: StudyTagCategory;
  description: string;
  weight: number;
  sources: string[];
  related: string[];
}

export interface StudyData {
  generatedAt: string;
  documents: StudyDocument[];
  tags: StudyTag[];
}
