import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

function getScriptDir() {
  return path.dirname(fileURLToPath(import.meta.url));
}

function getBundleRoot() {
  return path.resolve(getScriptDir(), '../..');
}

function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (!match) {
    return null;
  }

  const result = new Map();
  for (const line of match[1].split(/\r?\n/)) {
    const entry = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!entry) {
      continue;
    }
    result.set(entry[1], entry[2].trim().replace(/^['"]|['"]$/g, ''));
  }
  return result;
}

function listFiles(dirPath, predicate) {
  if (!fs.existsSync(dirPath)) {
    return [];
  }
  return fs.readdirSync(dirPath)
    .filter(name => predicate(name))
    .map(name => path.join(dirPath, name));
}

function parseAgentList(value) {
  if (!value) {
    return [];
  }
  const match = value.match(/^\[(.*)\]$/);
  if (!match) {
    return [];
  }
  return match[1]
    .split(',')
    .map(item => item.trim().replace(/^['"]|['"]$/g, ''))
    .filter(Boolean);
}

function validateBundle() {
  const root = getBundleRoot();
  const errors = [];

  const agentFiles = listFiles(path.join(root, 'agents'), name => name.endsWith('.agent.md'));
  const promptFiles = listFiles(path.join(root, 'prompts'), name => name.endsWith('.prompt.md'));
  const instructionFiles = listFiles(path.join(root, 'instructions'), name => name.endsWith('.instructions.md'));

  const knownAgents = new Set();

  for (const filePath of agentFiles) {
    const frontmatter = parseFrontmatter(fs.readFileSync(filePath, 'utf8'));
    if (!frontmatter) {
      errors.push(`Missing frontmatter in ${path.basename(filePath)}`);
      continue;
    }
    const name = frontmatter.get('name');
    if (!name) {
      errors.push(`Missing name in ${path.basename(filePath)}`);
      continue;
    }
    if (!frontmatter.get('description')) {
      errors.push(`Missing description in ${path.basename(filePath)}`);
    }
    knownAgents.add(name);
  }

  for (const filePath of agentFiles) {
    const frontmatter = parseFrontmatter(fs.readFileSync(filePath, 'utf8'));
    if (!frontmatter) {
      continue;
    }
    for (const referencedAgent of parseAgentList(frontmatter.get('agents'))) {
      if (!knownAgents.has(referencedAgent)) {
        errors.push(`Unknown agent '${referencedAgent}' referenced in ${path.basename(filePath)}`);
      }
    }
  }

  for (const filePath of promptFiles) {
    const frontmatter = parseFrontmatter(fs.readFileSync(filePath, 'utf8'));
    if (!frontmatter) {
      errors.push(`Missing frontmatter in ${path.basename(filePath)}`);
      continue;
    }
    if (!frontmatter.get('description')) {
      errors.push(`Missing description in ${path.basename(filePath)}`);
    }
    const agentName = frontmatter.get('agent');
    if (agentName && !knownAgents.has(agentName)) {
      errors.push(`Unknown prompt agent '${agentName}' in ${path.basename(filePath)}`);
    }
  }

  for (const filePath of instructionFiles) {
    const frontmatter = parseFrontmatter(fs.readFileSync(filePath, 'utf8'));
    if (!frontmatter) {
      errors.push(`Missing frontmatter in ${path.basename(filePath)}`);
      continue;
    }
    if (!frontmatter.get('description')) {
      errors.push(`Missing description in ${path.basename(filePath)}`);
    }
  }

  const skillsRoot = path.join(root, 'skills');
  if (fs.existsSync(skillsRoot)) {
    for (const entry of fs.readdirSync(skillsRoot, { withFileTypes: true })) {
      if (!entry.isDirectory()) {
        continue;
      }
      const skillPath = path.join(skillsRoot, entry.name, 'SKILL.md');
      if (!fs.existsSync(skillPath)) {
        errors.push(`Missing SKILL.md in skill folder ${entry.name}`);
        continue;
      }
      const frontmatter = parseFrontmatter(fs.readFileSync(skillPath, 'utf8'));
      if (!frontmatter) {
        errors.push(`Missing frontmatter in ${entry.name}/SKILL.md`);
        continue;
      }
      if (frontmatter.get('name') !== entry.name) {
        errors.push(`Skill name mismatch in ${entry.name}/SKILL.md`);
      }
      if (!frontmatter.get('description')) {
        errors.push(`Missing description in ${entry.name}/SKILL.md`);
      }
    }
  }

  return { root, errors, agentCount: knownAgents.size, promptCount: promptFiles.length };
}

const result = validateBundle();

if (result.errors.length > 0) {
  console.error(`Bundle validation failed for ${result.root}`);
  for (const error of result.errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`Bundle validation passed for ${result.root} (${result.agentCount} agents, ${result.promptCount} prompts).`);