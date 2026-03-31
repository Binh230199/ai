import path from 'path';
import {
  formatErrors,
  getDefaultManifestPath,
  readJsonIfExists,
  validateFinalGuide,
  validateManifest,
} from './runtime-validation-lib.mjs';

const manifestPath = getDefaultManifestPath();
const errors = validateManifest(manifestPath);
const manifest = readJsonIfExists(manifestPath);

if (manifest?.outputFile) {
  errors.push(...validateFinalGuide(path.resolve(manifest.outputFile)));
}

if (errors.length > 0) {
  process.stdout.write(JSON.stringify({
    systemMessage: `Final output validation found issues:\n${formatErrors(errors)}`,
  }));
} else {
  process.stdout.write(JSON.stringify({
    systemMessage: 'Final output validation passed or no runtime artifacts were present yet.',
  }));
}
