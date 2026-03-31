import fs from 'fs';
import path from 'path';

export function normalizeSlashes(value) {
  return value.replace(/\\/g, '/');
}

export function getWorkspaceRoot() {
  return process.cwd();
}

export function getDefaultArtifactRoot() {
  return path.join(getWorkspaceRoot(), 'artifacts', 'cpp-standards-guideline');
}

export function getDefaultManifestPath() {
  return path.join(getDefaultArtifactRoot(), 'manifest.json');
}

export function readJsonIfExists(filePath) {
  if (!fs.existsSync(filePath)) {
    return null;
  }
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

export function collectCandidatePaths(payload) {
  const values = new Set();

  function visit(node) {
    if (node === null || node === undefined) {
      return;
    }
    if (typeof node === 'string') {
      values.add(node);
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
  return Array.from(values);
}

export function validateJsonFile(filePath) {
  try {
    JSON.parse(fs.readFileSync(filePath, 'utf8'));
    return [];
  } catch (error) {
    return [`Invalid JSON in ${normalizeSlashes(filePath)}: ${error.message}`];
  }
}

export function validateManifest(manifestPath) {
  const errors = [];
  if (!fs.existsSync(manifestPath)) {
    return errors;
  }

  let manifest;
  try {
    manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  } catch (error) {
    return [`Invalid manifest JSON in ${normalizeSlashes(manifestPath)}: ${error.message}`];
  }

  for (const field of ['standardName', 'sourceDocument', 'artifactRoot', 'outputFile', 'status', 'phases']) {
    if (!(field in manifest)) {
      errors.push(`Missing '${field}' in ${normalizeSlashes(manifestPath)}`);
    }
  }

  return errors;
}

export function validateFinalGuide(guidePath) {
  const errors = [];
  if (!fs.existsSync(guidePath)) {
    return errors;
  }

  const content = fs.readFileSync(guidePath, 'utf8');
  const requiredSections = [
    '# ',
    '## Source and Scope',
    '## Analysis Method',
    '## Core Rule Families',
    '## Preferred Canonical Patterns',
    '## Rule Interaction Map',
    '## Fix-Order Strategy',
    '## Review Checklist',
    '## Rule Index',
  ];

  for (const section of requiredSections) {
    if (!content.includes(section)) {
      errors.push(`Missing section '${section}' in ${normalizeSlashes(guidePath)}`);
    }
  }

  return errors;
}

export function formatErrors(errors) {
  return errors.map(error => `- ${error}`).join('\n');
}
