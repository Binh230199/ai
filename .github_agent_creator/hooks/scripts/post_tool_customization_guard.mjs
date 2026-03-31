import fs from 'fs';
import { collectCandidatePaths, formatErrors, validateCustomizationFile } from './customization-validation-lib.mjs';

function readPayload() {
  try {
    const text = fs.readFileSync(0, 'utf8').trim();
    return text ? JSON.parse(text) : {};
  } catch {
    return {};
  }
}

const payload = readPayload();
const candidatePaths = collectCandidatePaths(payload);
const results = candidatePaths.map(filePath => ({ filePath, errors: validateCustomizationFile(filePath) }));
const failing = results.filter(result => result.errors.length > 0);

if (failing.length > 0) {
  process.stdout.write(JSON.stringify({
    decision: 'block',
    systemMessage: `Customization validation failed:\n${formatErrors(failing)}`,
  }));
} else {
  process.stdout.write('{}');
}
