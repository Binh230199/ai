import fs from 'fs';
import path from 'path';

const CUSTOMIZATION_SUFFIXES = [
  '.instructions.md',
  '.prompt.md',
  '.agent.md',
  '/SKILL.md',
  '\\SKILL.md',
  '/copilot-instructions.md',
  '\\copilot-instructions.md',
  '/AGENTS.md',
  '\\AGENTS.md',
  '.json',
  '.mjs',
];

export function normalizeSlashes(value) {
  return value.replace(/\\/g, '/');
}

export function isCustomizationPath(filePath) {
  const normalized = normalizeSlashes(filePath);
  const isUnderGithub = normalized.includes('/.github/') || normalized.startsWith('.github/');
  return isUnderGithub && CUSTOMIZATION_SUFFIXES.some(suffix => normalized.endsWith(suffix));
}

export function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (!match) {
    return null;
  }

  const result = {};
  for (const line of match[1].split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) {
      continue;
    }
    const entry = trimmed.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!entry) {
      continue;
    }
    result[entry[1]] = entry[2].replace(/^['"]|['"]$/g, '');
  }
  return result;
}

export function collectCandidatePaths(payload) {
  const values = new Set();

  function visit(node) {
    if (node === null || node === undefined) {
      return;
    }
    if (typeof node === 'string') {
      const normalized = normalizeSlashes(node);
      if (normalized.includes('/.github/') || normalized.startsWith('.github/')) {
        values.add(normalized);
      }
      return;
    }
    if (Array.isArray(node)) {
      for (const item of node) {
        visit(item);
      }
      return;
    }
    if (typeof node === 'object') {
      for (const value of Object.values(node)) {
        visit(value);
      }
    }
  }

  visit(payload);
  return Array.from(values).filter(isCustomizationPath);
}

export function validateCustomizationFile(filePath) {
  const absolutePath = path.resolve(filePath);
  const normalized = normalizeSlashes(filePath);
  const errors = [];

  if (!fs.existsSync(absolutePath)) {
    errors.push(`File does not exist: ${normalized}`);
    return errors;
  }

  if (normalized.endsWith('.json')) {
    try {
      JSON.parse(fs.readFileSync(absolutePath, 'utf8'));
    } catch (error) {
      errors.push(`Invalid JSON in ${normalized}: ${error.message}`);
    }
    return errors;
  }

  if (normalized.endsWith('.mjs')) {
    return errors;
  }

  if (normalized.endsWith('/copilot-instructions.md') || normalized.endsWith('/AGENTS.md')) {
    const content = fs.readFileSync(absolutePath, 'utf8').trim();
    if (!content) {
      errors.push(`${normalized} must not be empty.`);
    }
    return errors;
  }

  const content = fs.readFileSync(absolutePath, 'utf8');
  const frontmatter = parseFrontmatter(content);
  if (!frontmatter) {
    errors.push(`Missing YAML frontmatter in ${normalized}`);
    return errors;
  }

  if (!frontmatter.description) {
    errors.push(`Missing 'description' in ${normalized}`);
  }

  if (normalized.endsWith('/SKILL.md')) {
    if (!frontmatter.name) {
      errors.push(`Missing 'name' in ${normalized}`);
    } else {
      const expectedName = path.basename(path.dirname(absolutePath));
      if (frontmatter.name !== expectedName) {
        errors.push(`Skill name '${frontmatter.name}' does not match folder '${expectedName}' in ${normalized}`);
      }
    }
  }

  return errors;
}

export function scanCustomizationBundle(rootDir = '.github') {
  const results = [];

  function walk(currentDir) {
    if (!fs.existsSync(currentDir)) {
      return;
    }
    for (const entry of fs.readdirSync(currentDir, { withFileTypes: true })) {
      const fullPath = path.join(currentDir, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
        continue;
      }
      if (isCustomizationPath(fullPath)) {
        results.push({ filePath: normalizeSlashes(fullPath), errors: validateCustomizationFile(fullPath) });
      }
    }
  }

  walk(rootDir);
  return results;
}

export function formatErrors(results) {
  const lines = [];
  for (const result of results) {
    for (const error of result.errors) {
      lines.push(`- ${error}`);
    }
  }
  return lines.join('\n');
}
