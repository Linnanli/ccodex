// Submit/read one dedicated read-only fixture task in the owned desktop instance.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { chromium } from '/private/tmp/ccodex-rea-tooling/install/node_modules/playwright-core/index.mjs';

const workspace = path.resolve(import.meta.dirname, '../..');
const action = process.argv[2];
const name = process.argv[3] || action;
if (!['submit', 'read'].includes(action) || !/^[a-z0-9-]{1,40}$/.test(name)) throw Error('Invalid task action/name');
const session = JSON.parse(await fs.readFile(path.join(workspace, '.analysis-local/current-runtime.json'), 'utf8'));
const fixture = JSON.parse(await fs.readFile(path.join(workspace, '.analysis-local/current-project-fixture.json'), 'utf8'));
if (fixture.runtimePid !== session.pid || !fixture.projectId || !fixture.projectSetupVerifiedAtUtc) throw Error('Verified owned fixture required');
const actual = execFileSync('/bin/ps', ['-p', String(session.pid), '-o', 'comm='], { encoding: 'utf8' }).trim();
if (actual !== path.join(session.runtimeApplication, 'Contents/MacOS/ChatGPT')) throw Error('Owned runtime no longer live');
const out = path.join(workspace, 'analysis', session.baselineId);
const destination = path.join(out, 'runtime-artifacts/owned-task-' + name + '.json');
try { await fs.access(destination); throw Error('Preserve earlier task observation'); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
const prompt = 'CCODEX_DESKTOP_ANALYSIS_01：只读取当前项目的 README.md，不执行命令、不修改文件。请回复文件中 Sentinel 行的原文，再用一句话说明文件内容。';
const expectedReply = 'Sentinel: CCODEX_OWNED_FIXTURE_01';
const record = { baselineId: session.baselineId, action: 'owned-task-' + action, observationName: name,
  observedAtUtc: new Date().toISOString(), method: 'playwright-cdp-owned-desktop-read-only-model-task',
  runtimePid: session.pid, status: 'observed', fixtureSnapshot: fixture, prompt,
  observations: {}, limitations: ['Only this owned task prompt, fixed product controls and expected fixture output are inspected.',
    'This single read-only model task does not cover writes, approvals, PTY, cancellation, cloud hosts or all features.',
    'The earlier project setup used host RPC; it is not verification of the project creation UI workflow.',
    'Separate profile and CODEX_HOME do not establish separate authentication.'] };
const source = await fs.readFile(import.meta.filename);
const sourceSnapshot = path.join(out, 'raw/desktop-task/runner-' + name + '.mjs');
await fs.mkdir(path.dirname(sourceSnapshot), { recursive: true });
await fs.writeFile(sourceSnapshot, source, { flag: 'wx' });
record.runner = { path: path.relative(out, sourceSnapshot), sha256: crypto.createHash('sha256').update(source).digest('hex') };
const browser = await chromium.connectOverCDP(session.debugEndpoint);
try {
  const pages = browser.contexts().flatMap(c => c.pages()).filter(p => p.url().startsWith('app://-/'));
  let page;
  if (action === 'submit') page = pages.find(p => p.url() === 'app://-/index.html');
  else {
    const matches = [];
    for (const candidate of pages) if (await candidate.getByText(prompt, { exact: true }).count()) matches.push(candidate);
    if (matches.length !== 1) throw Error('Expected exactly one owned task page');
    page = matches[0];
  }
  if (!page) throw Error('Owned task application page missing');
  if (action === 'submit') {
    const editor = page.getByRole('textbox', { name: '随心输入', exact: true });
    if (await page.getByText(fixture.name, { exact: true }).count() === 0) throw Error('Owned project label missing');
    if (await editor.count() !== 1 || (await editor.innerText()).trim()) throw Error('Do not replace a nonempty composer');
    await editor.fill(prompt);
    await editor.press('Enter');
    record.steps = ['Fill the empty composer with the dedicated read-only task prompt.', 'Press Enter once.'];
    await page.waitForTimeout(1000);
    record.observations.composerCleared = await editor.count() === 1 && (await editor.innerText()).trim() === '';
    record.observations.ownPromptOccurrences = await page.getByText(prompt, { exact: true }).count();
    record.observations.submissionIndicated = record.observations.composerCleared && record.observations.ownPromptOccurrences > 0;
  } else {
    record.observations.ownPromptOccurrences = await page.getByText(prompt, { exact: true }).count();
    record.observations.expectedReplyExactOccurrences = await page.getByText(expectedReply, { exact: true }).count();
    record.observations.expectedReplySubstringOccurrences = await page.getByText(expectedReply, { exact: false }).count();
    if (record.observations.expectedReplyExactOccurrences === 1) {
      const expectedElement = page.getByText(expectedReply, { exact: true });
      const markdown = expectedElement.locator('xpath=ancestor::div[contains(@class, "_MarkdownRoot_")][1]');
      if (await markdown.count() !== 1) throw Error('Expected one bounded reply MarkdownRoot');
      const reply = await markdown.innerText();
      if (reply.length > 500 || !reply.includes(expectedReply)) throw Error('Reply exceeds owned fixture scope');
      record.observations.ownedReplyMarkdownText = reply;
      record.observations.ownedReplyVisible = await expectedElement.isVisible();
      record.observations.replyTextScope = 'Nearest MarkdownRoot ancestor of the unique expected synthetic Sentinel element on the owned prompt page.';
    }
    record.observations.productControlCounts = {};
    for (const label of ['停止', '停止生成', '停止任务', '取消', 'Stop', 'Stop generating', 'Stop task']) {
      record.observations.productControlCounts[label] = await page.getByRole('button', { name: label, exact: true }).count();
    }
    record.observations.ownProjectLabelOccurrences = await page.getByText(fixture.name, { exact: true }).count();
  }
  record.observations.pageUrl = page.url();
  const readme = await fs.readFile(path.join(fixture.root, 'README.md'));
  record.observations.fixtureReadmeUnchanged = crypto.createHash('sha256').update(readme).digest('hex') === fixture.files[0].sha256;
} catch (error) {
  record.status = 'failed';
  record.failure = error.message;
} finally {
  await fs.mkdir(path.dirname(destination), { recursive: true });
  await fs.writeFile(destination, JSON.stringify(record, null, 2) + '\n', { flag: 'wx' });
  await browser.close();
}
console.log(JSON.stringify({ path: destination, status: record.status, observations: record.observations, failure: record.failure }));
if (record.status === 'failed') process.exitCode = 1;
