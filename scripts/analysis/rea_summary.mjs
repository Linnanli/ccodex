// Stream the complete REA evidence; keep metadata without loading its graphs.
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import chain from '/private/tmp/ccodex-rea-tooling/install/node_modules/stream-chain/src/node/index.js';
import {parser} from '/private/tmp/ccodex-rea-tooling/install/node_modules/stream-json/src/index.js';
import {filter} from '/private/tmp/ccodex-rea-tooling/install/node_modules/stream-json/src/filters/filter.js';
import {streamValues} from '/private/tmp/ccodex-rea-tooling/install/node_modules/stream-json/src/streamers/stream-values.js';

const workspace = path.resolve(import.meta.dirname, '../..');
const baseline = JSON.parse(await fsp.readFile(path.join(workspace, '.analysis-local/current-baseline.json'), 'utf8'));
const directory = path.join(workspace, 'analysis', baseline.baselineId);
const input = process.argv[2] || path.join(directory, 'raw/rea-application-observed.json');
const output = process.argv[3] || path.join(directory, 'rea-summary.json');
const counts = {'graph.nodes': 0, 'graph.edges': 0, 'semantic_graph.nodes': 0, 'semantic_graph.relations': 0, 'semantic_graph.unknowns': 0};
const select = /^(evidence_id|subject|provider|parameters|limitations|normalized_result\.(input_path|format|root_artifact_sha256|inventory_manifest_id|inventory_graph_sha256|integrity_contradictions|summary|statistics|limitations|graph\.(schema|coverage|limitations|graph_id)|semantic_graph\.(schema|coverage|limitations|graph_id)))(\.|$)/;
const hash = crypto.createHash('sha256');
const source = fs.createReadStream(input);
let bytes = 0;
source.on('data', chunk => { hash.update(chunk); bytes += chunk.length; });
const pipeline = chain([source, parser(), filter({filter: (stack, token) => {
  if (stack.length === 4 && stack[0] === 'normalized_result' && token.name === 'startObject') {
    const name = stack.slice(1, 3).join('.');
    if (Object.hasOwn(counts, name)) counts[name] += 1;
  }
  return select.test(stack.join('.'));
}}), streamValues()]);
let metadata;
for await (const item of pipeline) {
  if (metadata !== undefined) throw new Error('Expected one root JSON object');
  metadata = item.value;
}
if (!metadata?.normalized_result || !metadata.evidence_id) throw new Error('Result lacks completed application Evidence');
const result = {baselineId: baseline.baselineId, sourcePath: input, sourceSha256: hash.digest('hex'), sourceBytes: bytes,
  summarizer: {script: 'scripts/analysis/rea_summary.mjs', method: 'stream-json 3.7.0; full token-stream parse, metadata selection and direct array-member counts'}, counts, evidence: metadata};
await fsp.writeFile(output, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify({output, counts, statistics: metadata.normalized_result.statistics,
  graphCoverage: metadata.normalized_result.graph.coverage,
  semanticCoverage: {status: metadata.normalized_result.semantic_graph.coverage.status,
    truncated: metadata.normalized_result.semantic_graph.coverage.truncated,
    omitted_nodes: metadata.normalized_result.semantic_graph.coverage.omitted_nodes,
    omitted_relations: metadata.normalized_result.semantic_graph.coverage.omitted_relations,
    limits: metadata.normalized_result.semantic_graph.coverage.limits}}, null, 2));
