// Return metadata only for the synthetic project's sidebar label.
import fs from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { chromium } from '/private/tmp/ccodex-rea-tooling/install/node_modules/playwright-core/index.mjs';
const workspace = path.resolve(import.meta.dirname, '../..');
const session = JSON.parse(await fs.readFile(path.join(workspace, '.analysis-local/current-runtime.json'), 'utf8'));
const fixture = JSON.parse(await fs.readFile(path.join(workspace, '.analysis-local/current-project-fixture.json'), 'utf8'));
const stored = JSON.parse(await fs.readFile(path.join(workspace, 'analysis', session.baselineId, 'runtime-artifacts/owned-task-storage-v2.json'), 'utf8'));
const observationName = process.argv[2] || 'owned-recovery-project-ancestor-handlers';
if (!/^[a-z0-9-]{1,60}$/.test(observationName)) throw Error('Invalid observation name');
if (session.baselineId !== fixture.baselineId) throw Error('Baseline mismatch');
if (execFileSync('/bin/ps', ['-p', String(session.pid), '-o', 'comm='], {encoding:'utf8'}).trim() !== path.join(session.runtimeApplication, 'Contents/MacOS/ChatGPT')) throw Error('Owned app required');
const browser = await chromium.connectOverCDP(session.debugEndpoint);
try {
  const pages = browser.contexts().flatMap(c => c.pages()).filter(p => p.url() === 'app://-/index.html');
  if (pages.length !== 1) throw Error('Unique owned app page required');
  const label = pages[0].locator('[data-marquee-text]').filter({hasText:new RegExp('^' + fixture.name + '$')});
  if (await label.count() !== 1) throw Error('Unique exact synthetic sidebar label required');
  const metadata = await label.evaluate(element => {
    const rows=[];
    for(let current=element, depth=0; current && depth<12; current=current.parentElement,depth++) {
      const key=Object.keys(current).find(k=>k.startsWith('__reactProps$'));
      const props=key ? current[key] : {};
      rows.push({depth,tag:current.tagName,role:current.getAttribute('role'),className:current.className,
        attributeNames:current.getAttributeNames(),ariaExpanded:current.getAttribute('aria-expanded'),
        dataState:current.getAttribute('data-state'),childCount:current.children.length,
        eventHandlerNames:Object.keys(props).filter(k=>/^on[A-Z]/.test(k) && typeof props[k] === 'function')});
    }
    return rows;
  });
  const ownedContainer = await label.evaluate((element, known) => {
    const root = element.closest('[data-sidebar-project-container-id]');
    if (!root) return {present:false};
    const rows = [...root.querySelectorAll('[data-app-action-sidebar-thread-id]')];
    return {present:true,containerIdMatchesProjectId:root.getAttribute('data-sidebar-project-container-id') === known.projectId,
      threadRowCount:rows.length,ownedThreadRowMatches:rows.filter(row => (row.getAttribute('data-app-action-sidebar-thread-id') || '').includes(known.threadId)).map(row => ({
        threadId:row.getAttribute('data-app-action-sidebar-thread-id'),tag:row.tagName,role:row.getAttribute('role'),
        attributeNames:row.getAttributeNames(),visible:!!(row.offsetWidth || row.offsetHeight || row.getClientRects().length)})),
      buttonCount:root.querySelectorAll('button,[role="button"]').length};
  }, {projectId:fixture.projectId,threadId:stored.observations.threadId});
  const record={baselineId:session.baselineId,runtimePid:session.pid,action:observationName,status:'observed',
    method:'playwright-cdp-exact-owned-label-ancestor-metadata-only',observedAtUtc:new Date().toISOString(),
    observations:{metadata,ownedContainer},limitations:['No surrounding text, credential values or unrelated history inspected. Handler names describe element structure, not navigation semantics.']};
  const dest=path.join(workspace,'analysis',session.baselineId,'runtime-artifacts/' + observationName + '.json');
  await fs.writeFile(dest,JSON.stringify(record,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify(record));
} finally {await browser.close();}
