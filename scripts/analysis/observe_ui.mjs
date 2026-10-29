// Observe only the task-owned CDP window and selected product controls.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { chromium } from '/private/tmp/ccodex-rea-tooling/install/node_modules/playwright-core/index.mjs';

const workspace = path.resolve(import.meta.dirname, '../..');
const session = JSON.parse(await fs.readFile(path.join(workspace, '.analysis-local/current-runtime.json'), 'utf8'));
const action = process.argv[2];
const name = process.argv[3] || action;
const actions = ['overview', 'work-location', 'permissions', 'model', 'project', 'settings', 'settings-menu', 'draft-fill', 'draft-read'];
if (!actions.includes(action) || !/^[a-zA-Z0-9_-]+$/.test(name)) throw new Error('Unknown observation action/name');
const out = path.join(workspace, 'analysis', session.baselineId, 'runtime-artifacts');
await fs.mkdir(out, { recursive: true });
const recordPath = path.join(out, name + '.json');
try { await fs.access(recordPath); throw new Error('Observation already exists; preserve it with a new name'); }
catch (e) { if (e.code !== 'ENOENT') throw e; }
const browser = await chromium.connectOverCDP(session.debugEndpoint);
const page = browser.contexts().flatMap(c => c.pages()).find(p => p.url() === 'app://-/index.html');
if (!page) throw new Error('Owned application page not found');
const draft = 'ccodex-behavior-draft-' + session.baselineId;
const record = {
  baselineId: session.baselineId, action, observedAtUtc: new Date().toISOString(),
  method: 'playwright-cdp-ui', endpoint: session.debugEndpoint, runtimePid: session.pid,
  profileDirectory: session.profileDirectory, codexHome: session.codexHome,
  url: page.url(), steps: [], observations: {}, limitations: [
    'Separate local paths do not establish separate authentication: the application automatically exposed an existing account/cloud history.',
    'Personal history and credential contents are excluded from this artifact.',
    'This is supplemental UI observation; REA 6.4.0 excludes app:// page targets.',
  ],
};
try {
  if (action === 'overview') {
    record.observations = {
      codexModeButton: await page.getByRole('button', { name: '切换模式，当前模式：Codex', exact: true }).count(),
      newTaskHeading: await page.getByText('我们要构建什么？', { exact: true }).count(),
      localLocation: await page.getByRole('button', { name: '工作位置', exact: true }).innerText(),
      permission: await page.getByRole('button', { name: '更改权限', exact: true }).innerText(),
      editableCount: await page.getByRole('textbox', { name: '随心输入', exact: true }).count(),
    };
  } else if (action === 'draft-fill' || action === 'draft-read') {
    const editor = page.getByRole('textbox', { name: '随心输入', exact: true });
    if (action === 'draft-fill') {
      if ((await editor.innerText()).trim()) throw new Error('Refusing to replace a nonempty editor');
      await editor.fill(draft);
      await editor.press('Tab');
      record.steps.push('Fill the empty new-task editor with the dedicated test sentinel, then blur; do not submit.');
    }
    const text = (await editor.innerText()).trim();
    record.observations = { matchesTestDraft: text === draft, textLength: text.length, expectedTestDraft: draft };
  } else if (action === 'settings' || action === 'settings-menu') {
    if (action === 'settings-menu') {
      await page.getByRole('button', { name: '打开个人资料菜单', exact: true }).click();
      await page.getByRole('menuitem', { name: /^设置/ }).click();
      record.steps.push('Open the profile menu and choose Settings; do not read or store profile identity.');
    } else {
      await page.keyboard.press('Meta+,');
      record.steps.push('Press the settings keyboard shortcut in the owned application page.');
    }
    record.observations = {
      headings: await page.locator('h1,h2,[role="heading"]').allTextContents(),
      tabNames: await page.getByRole('tab').allTextContents(),
      settingsLabels: await page.getByText('设置', { exact: true }).count(),
      appPageUrls: browser.contexts().flatMap(c => c.pages()).map(p => p.url()).filter(u => u.startsWith('app://')),
    };
  } else {
    const labels = { 'work-location': '工作位置', permissions: '更改权限', project: '选择项目' };
    const button = action === 'model'
      ? page.getByRole('button', { name: /^GPT-6\.1 Sol/ })
      : page.getByRole('button', { name: labels[action], exact: true });
    await button.click();
    record.steps.push('Open ' + action + ' control; read its popup; dismiss with Escape without changing selection.');
    const popup = page.locator('[role="menu"],[role="dialog"],[role="listbox"]').filter({ visible: true });
    await popup.first().waitFor({ state: 'visible', timeout: 10000 });
    record.observations.popups = await popup.evaluateAll(es => es.map(e => ({ role: e.getAttribute('role'), text: e.innerText })));
    const png = path.join(out, name + '.png');
    await popup.first().screenshot({ path: png });
    record.screenshot = { path: path.basename(png), sha256: crypto.createHash('sha256').update(await fs.readFile(png)).digest('hex') };
    await page.keyboard.press('Escape');
  }
  record.status = 'observed';
} catch (error) {
  record.status = 'failed';
  record.failure = String(error.message);
} finally {
  await fs.writeFile(recordPath, JSON.stringify(record, null, 2) + '\n');
  await browser.close();
}
console.log(JSON.stringify({ path: recordPath, status: record.status, observations: record.observations, failure: record.failure }));
if (record.status === 'failed') process.exitCode = 1;
