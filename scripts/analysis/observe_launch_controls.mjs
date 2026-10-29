import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from '/private/tmp/ccodex-rea-tooling/install/node_modules/playwright-core/index.mjs';

const workspace = path.resolve(import.meta.dirname, '../..');
const session = JSON.parse(await fs.readFile(path.join(workspace, '.analysis-local/current-runtime.json'), 'utf8'));
const runName = process.argv[2] || 'clean-launch-controls';
if (!/^[a-z0-9-]{1,40}$/.test(runName)) throw new Error('Invalid observation name');
const destination = path.join(workspace, 'analysis', session.baselineId, 'runtime-artifacts/' + runName + '.json');
try { await fs.access(destination); throw new Error('Preserve the earlier observation; destination already exists'); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
const browser = await chromium.connectOverCDP(session.debugEndpoint);
try {
  const page = browser.contexts().flatMap(context => context.pages()).find(page => page.url() === 'app://-/index.html');
  if (!page) throw new Error('Owned page missing');
  const labels = ['我们要构建什么？', '登录', '继续使用 ChatGPT', '使用 API 密钥', '设置', '此计算机', '云端', '远程',
    'What do you want to build?', 'Sign in', 'Sign in with ChatGPT', 'Continue with ChatGPT', 'Use an API key',
    'Log in', 'Codex', 'Settings', 'Local', 'Cloud', 'Remote'];
  const present = {};
  for (const label of labels) present[label] = await page.getByText(label, { exact: true }).count();
  const controls = {};
  for (const [key, role, name] of [
    ['codexMode', 'button', '切换模式，当前模式：Codex'], ['composer', 'textbox', '随心输入'],
    ['profileMenu', 'button', '打开个人资料菜单'], ['workLocation', 'button', '工作位置'],
    ['composerEnglish', 'textbox', 'Ask anything'], ['workLocationEnglish', 'button', 'Work location'],
    ['profileMenuEnglish', 'button', 'Open profile menu'],
  ]) controls[key] = await page.getByRole(role, { name, exact: true }).count();
  const structuralCounts = { buttons: await page.getByRole('button').count(), textboxes: await page.getByRole('textbox').count(),
    headings: await page.locator('h1,h2,[role="heading"]').count(), bodyTextLength: await page.locator('body').evaluate(element => element.textContent.length) };
  const record = { baselineId: session.baselineId, action: runName, observedAtUtc: new Date().toISOString(),
    method: 'playwright-cdp-ui', runtimePid: session.pid, environmentPolicy: session.environmentPolicy, present, controls,
    structuralCounts, status: 'observed', limitations: ['Only fixed product-label counts were read; no account identity, history or credential contents.',
      'No task was submitted; final startup environment and backend ownership require independent verification.'] };
  await fs.mkdir(path.dirname(destination), { recursive: true });
  await fs.writeFile(destination, JSON.stringify(record, null, 2) + '\n');
  console.log(JSON.stringify(record));
} finally { await browser.close(); }
