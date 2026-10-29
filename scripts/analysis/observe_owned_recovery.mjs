// Observe recovery of the one already authorized synthetic task. Never submit a task.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { chromium } from '/private/tmp/ccodex-rea-tooling/install/node_modules/playwright-core/index.mjs';

const workspace = path.resolve(import.meta.dirname, '../..');
const name = process.argv[2] || 'recovery-01';
if (!/^[a-z0-9-]{1,40}$/.test(name)) throw Error('Invalid recovery observation name');
const verificationName = process.argv[3] || name;
if (!/^[a-z0-9-]{1,40}$/.test(verificationName)) throw Error('Invalid process verification name');
const session = JSON.parse(await fs.readFile(path.join(workspace, '.analysis-local/current-runtime.json'), 'utf8'));
const out = path.join(workspace, 'analysis', session.baselineId);
const fixture = JSON.parse(await fs.readFile(path.join(workspace, '.analysis-local/current-project-fixture.json'), 'utf8'));
const original = JSON.parse(await fs.readFile(path.join(out, 'runtime-artifacts/owned-task-bounded-reply.json'), 'utf8'));
const stored = JSON.parse(await fs.readFile(path.join(out, 'runtime-artifacts/owned-task-storage-v2.json'), 'utf8'));
const verificationPath = 'runtime-process-verification-' + verificationName + '.json';
const verificationBytes = await fs.readFile(path.join(out, verificationPath));
const verified = JSON.parse(verificationBytes);
const actual = execFileSync('/bin/ps', ['-p', String(session.pid), '-o', 'comm='], { encoding: 'utf8' }).trim();
if (actual !== path.join(session.runtimeApplication, 'Contents/MacOS/ChatGPT')) throw Error('Owned restarted app is not live');
if (session.pid === original.runtimePid || verified.runtimePid !== session.pid || !verified.nativeCliFrozenInventoryMatch.matches) throw Error('Verified new runtime required');
if ([fixture, original, stored, verified].some(value => value.baselineId !== session.baselineId)) throw Error('Baseline mismatch');
if (session.codexHome !== '/private/tmp/ccodex-behavior/force-cli-01/codex-home' || session.profileDirectory !== '/private/tmp/ccodex-behavior/force-cli-01/user-data') throw Error('Previous owned profile and home required');
const threadId = stored.observations.threadId;
if (!/^[0-9a-f-]{36}$/.test(threadId) || stored.observations.ownedPromptCount !== 1) throw Error('Unique owned thread required');
const destination = path.join(out, 'runtime-artifacts/owned-task-' + name + '.json');
try { await fs.access(destination); throw Error('Preserve earlier recovery observation'); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
const runnerPath = path.join(out, 'raw/desktop-task/runner-' + name + '.mjs');
await fs.mkdir(path.dirname(runnerPath), { recursive: true });
const source = await fs.readFile(import.meta.filename);
await fs.writeFile(runnerPath, source, { flag: 'wx' });
const record = { baselineId: session.baselineId, action: 'owned-task-recovery', observationName: name,
  runtimePid: session.pid, priorRuntimePid: original.runtimePid, observedAtUtc: new Date().toISOString(),
  status: 'observed', method: 'playwright-cdp-owned-restarted-profile-single-existing-thread',
  processVerification: {path:verificationPath,sha256:crypto.createHash('sha256').update(verificationBytes).digest('hex')},
  runner: { path: path.relative(out, runnerPath), sha256: crypto.createHash('sha256').update(source).digest('hex') },
  observations: { threadId, newModelTasksSubmitted: 0 }, steps: [],
  limitations: ['Only the already authorized synthetic task, its exact prompt/reply and owned project label are inspected.',
    'Restoring one completed task does not verify interrupted execution, errors, approvals or every storage layer.',
    'Profile, CODEX_HOME and CLI identity do not establish authentication isolation.',
    'A visible sentinel alone is not a task-completion event; the original completed turn is independently identified.'] };
const browser = await chromium.connectOverCDP(session.debugEndpoint);
try {
  const pages = browser.contexts().flatMap(context => context.pages()).filter(page => page.url() === 'app://-/index.html');
  if (pages.length !== 1) throw Error('Expected one owned application page');
  const page = pages[0];
  const prompt = original.prompt;
  const expected = 'Sentinel: CCODEX_OWNED_FIXTURE_01';
  record.observations.initialOwnPromptOccurrences = await page.getByText(prompt, { exact: true }).count();
  record.observations.initialExpectedReplyOccurrences = await page.getByText(expected, { exact: true }).count();
  record.observations.ownProjectLabelOccurrences = await page.getByText(fixture.name, { exact: true }).count();
  if (!record.observations.initialOwnPromptOccurrences) {
    const link = page.locator('a[href*="' + threadId + '"]');
    record.observations.ownedThreadLinkCount = await link.count();
    if (record.observations.ownedThreadLinkCount === 1) {
      const href = await link.getAttribute('href');
      if (!href || !/^(?:\/|#|app:\/\/-\/|codex:\/\/)/.test(href) || !href.includes(threadId)) throw Error('Unexpected owned-thread navigation target');
      record.observations.ownedThreadHref = href;
      await link.click();
      record.steps.push('Open the unique observed local link containing the already owned thread UUID.');
    } else {
      // Use an observed identity from the exact synthetic project, never invent a route or ID prefix.
      const metadataPath = 'runtime-artifacts/owned-recovery-project-thread-attributes.json';
      const metadataBytes = await fs.readFile(path.join(out, metadataPath));
      const metadata = JSON.parse(metadataBytes);
      const container = metadata.observations.ownedContainer;
      if (metadata.baselineId !== session.baselineId || metadata.runtimePid !== session.pid || metadata.status !== 'observed' ||
          container.threadRowCount !== 1 || container.ownedThreadRowMatches.length !== 1) throw Error('Unique observed synthetic-project thread identity required');
      const rowId = container.ownedThreadRowMatches[0].threadId;
      if (rowId !== threadId && rowId !== 'local:' + threadId) throw Error('Observed row ID is not the owned task');
      record.observations.navigationIdentityEvidence = {path:metadataPath,sha256:crypto.createHash('sha256').update(metadataBytes).digest('hex'),observedRowId:rowId};
      const rowSelector = '[data-app-action-sidebar-thread-row][data-app-action-sidebar-thread-id="' + rowId + '"]';
      record.observations.globalOwnedSidebarThreadRowCount = await page.locator(rowSelector).count();
      const projectLabel = page.locator('[data-marquee-text]').filter({hasText:new RegExp('^' + fixture.name + '$')});
      if (await projectLabel.count() !== 1) throw Error('Unique synthetic project sidebar label required');
      const projectContainer = projectLabel.locator('xpath=ancestor::div[@data-sidebar-project-container-id][1]');
      if (await projectContainer.count() !== 1) throw Error('Unique synthetic project container required');
      const row = projectContainer.locator(rowSelector);
      record.observations.ownedSidebarThreadRowCount = await row.count();
      if (record.observations.ownedThreadLinkCount !== 0 || record.observations.ownedSidebarThreadRowCount !== 1) throw Error('Unique observed owned-thread row unavailable; no navigation guessed');
      if (!await row.isVisible()) throw Error('Owned-thread row is not visible');
      record.observations.ownedSidebarThreadIdExactMatch = await row.getAttribute('data-app-action-sidebar-thread-id') === rowId;
      await row.click();
      record.steps.push('Click the unique visible sidebar thread row with the exact already-owned thread UUID.');
    }
  } else record.steps.push('Observe the already restored owned task without navigation.');
  await page.getByText(prompt, { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  const sentinel = page.getByText(expected, { exact: true });
  await sentinel.waitFor({ state: 'visible', timeout: 10000 });
  if (await sentinel.count() !== 1) throw Error('Expected one owned reply element');
  const markdown = sentinel.locator('xpath=ancestor::div[contains(@class, "_MarkdownRoot_")][1]');
  if (await markdown.count() !== 1) throw Error('Expected one owned reply MarkdownRoot');
  const reply = await markdown.innerText();
  if (reply !== original.observations.ownedReplyMarkdownText) throw Error('Restored reply does not match the previously verified synthetic reply');
  record.observations.finalOwnPromptOccurrences = await page.getByText(prompt, { exact: true }).count();
  record.observations.restoredReplyExactMatch = true;
  record.observations.ownedReplyVisible = await sentinel.isVisible();
  record.observations.ownedReplyMarkdownText = reply;
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
