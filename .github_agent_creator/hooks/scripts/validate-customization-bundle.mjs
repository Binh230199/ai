import { formatErrors, scanCustomizationBundle } from './customization-validation-lib.mjs';

const results = scanCustomizationBundle('.github');
const failing = results.filter(result => result.errors.length > 0);

if (failing.length > 0) {
  process.stdout.write(JSON.stringify({
    systemMessage: `Customization bundle validation found issues:\n${formatErrors(failing)}`,
  }));
} else {
  process.stdout.write(JSON.stringify({
    systemMessage: `Customization bundle validation passed for ${results.length} files.`,
  }));
}
