// Read-only lexical classification with Babel; no release code is evaluated.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const [candidatePath, resultPath, parserPath] = process.argv.slice(2);
if (!candidatePath || !resultPath || !parserPath) throw new Error('Expected candidates, output, Babel parser path');
const require = createRequire(import.meta.url);
const parser = require(path.resolve(parserPath));
const candidates = JSON.parse(fs.readFileSync(candidatePath, 'utf8'));
const output = fs.openSync(resultPath, 'w');
let count = 0;
for (const candidate of candidates) {
  const text = fs.readFileSync(candidate.physicalPath, 'utf8');
  const record = { sourcePath: candidate.sourcePath, status: 'parsed', comments: [], errors: [] };
  try {
    const result = parser.parse(text, {
      sourceType: 'unambiguous', errorRecovery: true, attachComment: false,
      allowReturnOutsideFunction: true, allowAwaitOutsideFunction: true,
      allowNewTargetOutsideFunction: true, allowUndeclaredExports: true,
      plugins: ['jsx'],
    });
    for (const comment of result.comments || []) {
      if (!comment.value.includes('sourceMappingURL')) continue;
      record.comments.push({ type: comment.type,
        byteStart: Buffer.byteLength(text.slice(0, comment.start), 'utf8'),
        byteEnd: Buffer.byteLength(text.slice(0, comment.end), 'utf8') });
    }
    record.errors = (result.errors || []).map(error => ({ message: error.message, position: error.pos }));
    if (record.errors.length) record.status = 'parsed-with-recovered-errors';
  } catch (error) {
    record.status = 'parse-failed';
    record.errors = [{ message: error.message, position: error.pos }];
  }
  fs.writeSync(output, JSON.stringify(record) + '\n');
  if (++count % 500 === 0) process.stdout.write(JSON.stringify({ classified: count, total: candidates.length }) + '\n');
}
fs.closeSync(output);
process.stdout.write(JSON.stringify({ completed: count, total: candidates.length }) + '\n');
