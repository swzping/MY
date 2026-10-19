import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
let service;
let expo;
let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  service?.kill('SIGTERM');
  expo?.kill('SIGTERM');
  process.exitCode = code;
}
process.on('SIGINT', () => stop());
process.on('SIGTERM', () => stop());
async function healthy() {
  try {
    const result = await fetch('http://127.0.0.1:8787/health', { signal: AbortSignal.timeout(700) });
    return (await result.json()).service === 'jizhang-excel-sync';
  } catch { return false; }
}
if (!(await healthy())) {
  service = spawn('python3', ['scripts/excel_sync.py'], { cwd: root, stdio: 'inherit' });
  service.on('error', (error) => { console.error(error.message); stop(1); });
  service.on('exit', (code) => { if (!stopping) stop(code || 1); });
  for (let attempt = 0; attempt < 30 && !stopping && !(await healthy()); attempt++) {
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  if (!(await healthy())) { console.error('表格同步服务启动失败'); stop(1); }
}
if (!stopping) {
  expo = spawn(process.execPath, ['node_modules/expo/bin/cli', 'start', '--web', '--localhost', ...process.argv.slice(2)], { cwd: root, stdio: 'inherit' });
  expo.on('error', (error) => { console.error(error.message); stop(1); });
  expo.on('exit', (code) => stop(code || 0));
}
