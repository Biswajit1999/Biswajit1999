import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const DATA_PATH = path.join(ROOT, 'data', 'profile-evidence.json');
export const MARKDOWN_PATH = path.join(ROOT, 'EVIDENCE.md');

const requiredProjectFields = [
  'rank', 'slug', 'title', 'version', 'sourceRef', 'question', 'result', 'boundary',
  'repositoryUrl', 'releaseUrl', 'liveUrl',
];

export function loadEvidence() {
  return JSON.parse(fs.readFileSync(DATA_PATH, 'utf8'));
}

export function validateEvidence(document) {
  const failures = [];
  if (document.schemaVersion !== 1) failures.push('schemaVersion must be 1');
  const projects = document.projects;
  if (!Array.isArray(projects) || projects.length === 0) failures.push('projects must be a non-empty array');
  const safeProjects = Array.isArray(projects) ? projects : [];
  if (document.evidenceIndex?.upstreamEvidenceRecords !== safeProjects.length) failures.push('evidenceIndex.upstreamEvidenceRecords must equal project count');
  if (!String(document.evidenceIndex?.boundary || '').includes('discovery links')) failures.push('evidence index boundary must distinguish discovery links');

  const slugs = new Set();
  for (const [index, project] of safeProjects.entries()) {
    for (const field of requiredProjectFields) {
      if (project[field] === undefined || project[field] === '') failures.push(`projects[${index}].${field} is required`);
    }
    if (slugs.has(project.slug)) failures.push(`duplicate project slug: ${project.slug}`);
    slugs.add(project.slug);
    if (!/^v/.test(project.version)) failures.push(`${project.slug}: version must start with v`);
    if (!project.releaseUrl.endsWith(`/releases/tag/${project.version}`)) failures.push(`${project.slug}: release URL does not match version`);
    for (const field of ['repositoryUrl', 'releaseUrl', 'liveUrl']) {
      if (!String(project[field]).startsWith('https://')) failures.push(`${project.slug}: ${field} must use HTTPS`);
    }
    if (String(project.boundary).length < 60) failures.push(`${project.slug}: boundary is too short`);
  }

  if (failures.length) throw new Error(failures.join('\n'));
}

const escapeMarkdown = text => String(text).replaceAll('|', '\\|');

export function renderMarkdown(document) {
  const sections = document.projects.map(project => `## ${project.title} · ${project.version}

**Research question.** ${project.question}

**Generated result.** ${project.result}

**Boundary of inference.** ${project.boundary}

[Repository](${project.repositoryUrl}) · [Versioned release](${project.releaseUrl}) · [Live evidence](${project.liveUrl}) · source \`${project.sourceRef}\`
`).join('\n');
  return `# Verified research evidence routed by this profile

This index is generated from [profile-evidence.json](data/profile-evidence.json), pinned to central registry [${document.sourceRegistry.version}](${document.sourceRegistry.url}). It exposes ${document.evidenceIndex.upstreamEvidenceRecords} upstream evidence records.

> ${document.evidenceIndex.boundary}

| Project | Release | Question | Result boundary |
| --- | --- | --- | --- |
${document.projects.map(project => `| [${escapeMarkdown(project.title)}](${project.repositoryUrl}) | [${project.version}](${project.releaseUrl}) | ${escapeMarkdown(project.question)} | ${escapeMarkdown(project.boundary)} |`).join('\n')}

${sections}
## Provenance

- Verified: ${document.verifiedDate}
- Profile evidence release: ${document.profileRelease}
- Central registry: [${document.sourceRegistry.version}](${document.sourceRegistry.dataUrl})
`;
}

export function outputs(document) {
  validateEvidence(document);
  return new Map([[MARKDOWN_PATH, renderMarkdown(document)]]);
}

function main() {
  const check = process.argv.includes('--check');
  const document = loadEvidence();
  const generated = outputs(document);
  const stale = [];
  for (const [file, content] of generated) {
    if (check) {
      if (!fs.existsSync(file) || fs.readFileSync(file, 'utf8') !== content) stale.push(path.relative(ROOT, file));
    } else {
      fs.writeFileSync(file, content, 'utf8');
      console.log(`Wrote ${path.relative(ROOT, file)}`);
    }
  }
  if (stale.length) {
    console.error(`Stale generated evidence: ${stale.join(', ')}`);
    process.exit(1);
  }
  if (check) console.log(`Profile evidence is current: ${generated.size} generated files, ${document.projects.length} routed records.`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
