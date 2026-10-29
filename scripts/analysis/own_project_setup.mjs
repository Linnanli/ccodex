// Set up one owned fixture through the source-confirmed host project service.
// This is API setup for later UI tests, not verification of the project dialog.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { chromium } from '/private/tmp/ccodex-rea-tooling/install/node_modules/playwright-core/index.mjs';

const workspace = path.resolve(import.meta.dirname, '../..');
const action = process.argv[2];
if (!['start', 'status', 'review-trust', 'trust'].includes(action)) throw Error('Unknown setup action');
const session = JSON.parse(await fs.readFile(path.join(workspace, '.analysis-local/current-runtime.json'), 'utf8'));
const expected = path.join(session.runtimeApplication, 'Contents/MacOS/ChatGPT');
const actual = execFileSync('/bin/ps', ['-p', String(session.pid), '-o', 'comm='], { encoding: 'utf8' }).trim();
if (actual !== expected || session.environmentPolicy !== 'allowlist-force-cli') throw Error('Owned isolated runtime required');
const out = path.join(workspace, 'analysis', session.baselineId);
const processVerification = JSON.parse(await fs.readFile(path.join(out, 'runtime-process-verification-frozen-match.json'), 'utf8'));
if (processVerification.runtimePid !== session.pid || !processVerification.nativeCliFrozenInventoryMatch.matches) throw Error('Verified frozen CLI required');
const fixtureRecordPath = path.join(workspace, '.analysis-local/current-project-fixture.json');
let fixture;
if (action === 'start') {
  try { await fs.access(fixtureRecordPath); throw Error('Preserve existing project fixture'); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  const id = crypto.randomUUID();
  const root = '/private/tmp/ccodex-behavior/projects/' + id;
  await fs.mkdir(path.dirname(root), { recursive: true });
  await fs.mkdir(root); // Exclusive creation: do not reuse a preexisting folder.
  const contents = '# Owned reverse-engineering fixture\n\nSentinel: CCODEX_OWNED_FIXTURE_01\n';
  await fs.writeFile(path.join(root, 'README.md'), contents, { flag: 'wx' });
  fixture = { baselineId: session.baselineId, runtimePid: session.pid, createdAtUtc: new Date().toISOString(),
    uuid: id, root, name: 'ccodex-analysis-' + id.slice(0, 8),
    files: [{ path: 'README.md', sha256: crypto.createHash('sha256').update(contents).digest('hex') }],
    setupMethod: 'source-confirmed-host-project-service-RPC',
    limitations: ['Setup is an API call, not the project creation UI workflow.',
      'Thread reassignment also consults saved hints. A fresh UUID assumes no historical cwd or hint uses this previously absent path or its canonical alias.',
      'Separate directories and the CLI executable check do not prove separate authentication.'] };
  await fs.writeFile(fixtureRecordPath, JSON.stringify(fixture, null, 2) + '\n', { flag: 'wx' });
} else fixture = JSON.parse(await fs.readFile(fixtureRecordPath, 'utf8'));
if (fixture.runtimePid !== session.pid || fixture.baselineId !== session.baselineId) throw Error('Fixture runtime differs');
const recordPath = path.join(out, 'runtime-artifacts/owned-project-' + action + '.json');
try { await fs.access(recordPath); throw Error('Preserve earlier observation'); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
const browser = await chromium.connectOverCDP(session.debugEndpoint);
const record = { baselineId: session.baselineId, action: 'owned-project-' + action, runtimePid: session.pid,
  observedAtUtc: new Date().toISOString(), method: 'playwright-cdp-source-confirmed-host-RPC-setup',
  status: 'observed', fixtureRoot: fixture.root, fixtureName: fixture.name,
  observations: {}, limitations: fixture.limitations };
try {
  const page = browser.contexts().flatMap(c => c.pages()).find(p => p.url() === 'app://-/index.html');
  if (!page) throw Error('Owned application page missing');
  if (action === 'start') {
    record.observations = await page.evaluate(async ({ root, name }) => {
      if (Object.hasOwn(window, '__ccodexOwnedProjectSetup')) throw Error('Own setup already exists');
      const module = await import('app://-/assets/app-initial-6350d04672d0.js');
      if (typeof module.Mln !== 'function') throw Error('Source-confirmed project factory missing');
      window.__ccodexOwnedProjectSetup = { status: 'pending' };
      const promise = module.Mln().createLocal({ appearance: null, initializeDefaultWorkspaceGitRepository: false,
        name, sources: [root], setActive: true });
      Promise.resolve(promise).then(result => {
        window.__ccodexOwnedProjectSetup = result === null ? { status: 'cancelled' } : {
          status: 'fulfilled', projectId: result.projectId,
          rootPathsMatch: Array.isArray(result.rootPaths) && result.rootPaths.length === 1 && result.rootPaths[0] === root,
        };
      }, error => { window.__ccodexOwnedProjectSetup = { status: 'rejected', errorName: error.name }; });
      return { invocationStarted: true, sources: [root], setActive: true };
    }, { root: fixture.root, name: fixture.name });
  } else if (action === 'trust' || action === 'review-trust') {
    const dialog = page.getByRole('dialog').filter({ hasText: fixture.uuid });
    const count = await dialog.count();
    record.observations = { ownFixtureDialogs: count };
    if (count !== 1) throw Error('Expected exactly one dialog containing the fresh fixture UUID');
    const text = await dialog.innerText();
    if (!text.includes(fixture.root)) throw Error('Dialog does not contain the complete owned source path');
    record.observations.dialogText = text;
    record.observations.buttonNames = await dialog.getByRole('button').allTextContents();
    const trust = dialog.getByRole('button', { name: /^(信任|信任文件夹|信任此文件夹|是，我信任此文件夹|Trust|Trust folder|Yes, I trust this folder)$/ });
    record.observations.matchedTrustButtons = await trust.count();
    if (action === 'trust') {
      if (record.observations.matchedTrustButtons !== 1) throw Error('Unambiguous product trust button was not found');
      await trust.click();
      record.observations.clickedOwnedFolderTrust = true;
    } else record.observations.clickedOwnedFolderTrust = false;
  } else {
    record.observations = await page.evaluate(() => window.__ccodexOwnedProjectSetup || { status: 'missing' });
    record.observations.ownProjectLabelCount = await page.getByText(fixture.name, { exact: true }).count();
    if (record.observations.status === 'fulfilled' && record.observations.rootPathsMatch) {
      fixture.projectId = record.observations.projectId;
      fixture.projectSetupVerifiedAtUtc = new Date().toISOString();
      await fs.writeFile(fixtureRecordPath, JSON.stringify(fixture, null, 2) + '\n');
    }
  }
} catch (error) {
  record.status = 'failed';
  record.failure = error.message;
} finally {
  await fs.mkdir(path.dirname(recordPath), { recursive: true });
  await fs.writeFile(recordPath, JSON.stringify(record, null, 2) + '\n', { flag: 'wx' });
  await browser.close();
}
console.log(JSON.stringify({ path: recordPath, status: record.status, observations: record.observations, failure: record.failure }));
if (record.status === 'failed') process.exitCode = 1;
