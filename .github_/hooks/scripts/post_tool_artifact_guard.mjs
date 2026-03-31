import fs from 'fs';
import path from 'path';
import {
  collectCandidatePaths,
  formatErrors,
  getDefaultManifestPath,
  readJsonIfExists,
  validateFinalGuide,
  validateJsonFile,
  validateManifest,
} from './runtime-validation-lib.mjs';

function readPayload() {
  try {
    const text = fs.readFileSync(0, 'utf8').trim();
    return text ? JSON.parse(text) : {};
  } catch {
    return {};
  }
}

const payload = readPayload();
const candidatePaths = collectCandidatePaths(payload).map(value => path.resolve(value));
const errors = [];

for (const filePath of candidatePaths) {
  if (!fs.existsSync(filePath)) {
    continue;
  }
  if (filePath.endsWith('.json')) {
    errors.push(...validateJsonFile(filePath));
  }
  if (/cpp-core-.*\.md$/i.test(filePath)) {
    errors.push(...validateFinalGuide(filePath));
  }
}

const manifestPath = getDefaultManifestPath();
errors.push(...validateManifest(manifestPath));

const manifest = readJsonIfExists(manifestPath);
if (manifest?.outputFile) {
  errors.push(...validateFinalGuide(path.resolve(manifest.outputFile)));
}

if (errors.length > 0) {
  process.stdout.write(JSON.stringify({
    decision: 'block',
    systemMessage: `Artifact validation failed:\n${formatErrors(errors)}`,
  }));
} else {
  process.stdout.write('{}');
}
