import { promises as fs } from 'node:fs';
import path from 'node:path';
import { buildStudyData, type MarkdownFile } from './study-taxonomy';

const root = path.resolve(process.cwd(), '..');
const studyDir = path.join(root, 'study');
const outputFile = path.join(process.cwd(), 'src/data/study-data.json');

async function main() {
  const files = await readMarkdownFiles(studyDir);
  const data = buildStudyData(files);
  await fs.mkdir(path.dirname(outputFile), { recursive: true });
  await fs.writeFile(outputFile, `${JSON.stringify(data, null, 2)}\n`, 'utf8');
  console.log(`Generated ${data.tags.length} tags from ${data.documents.length} documents.`);
}

async function readMarkdownFiles(dir: string): Promise<MarkdownFile[]> {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = await Promise.all(
    entries.map(async (entry) => {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) return readMarkdownFiles(fullPath);
      if (!entry.isFile() || !entry.name.endsWith('.md')) return [];
      const content = await fs.readFile(fullPath, 'utf8');
      return [{ path: path.relative(root, fullPath), content }];
    }),
  );
  return files.flat().sort((a, b) => a.path.localeCompare(b.path));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
