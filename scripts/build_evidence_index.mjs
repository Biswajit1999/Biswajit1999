import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const DATA_PATH = path.join(ROOT, 'data', 'profile-evidence.json');
export const MARKDOWN_PATH = path.join(ROOT, 'EVIDENCE.md');
export const CSV_PATH = path.join(ROOT, 'data', 'profile-evidence-maturity.csv');
export const SVG_PATH = path.join(ROOT, 'assets', 'profile-evidence-maturity.svg');

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
  if (document.programme?.upstreamEvidenceRecords !== safeProjects.length) failures.push('programme.upstreamEvidenceRecords must equal project count');
  if (document.programme?.completed > document.programme?.rankedQueue) failures.push('completed count cannot exceed ranked queue');
  if (!String(document.programme?.boundary || '').includes('discovery links')) failures.push('programme boundary must distinguish discovery links');

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

  const dimensions = document.maturity?.dimensions;
  if (!Array.isArray(dimensions) || dimensions.length < 6) failures.push('at least six maturity dimensions are required');
  const safeDimensions = Array.isArray(dimensions) ? dimensions : [];
  for (const dimension of safeDimensions) {
    if (!dimension.name || !Number.isInteger(dimension.before) || !Number.isInteger(dimension.after)) failures.push('invalid maturity dimension');
    else if (dimension.before < 0 || dimension.after > 100 || dimension.after <= dimension.before) failures.push(`${dimension.name}: scores must improve within 0-100`);
  }
  const mean = key => Math.round(safeDimensions.reduce((sum, item) => sum + item[key], 0) / safeDimensions.length);
  if (safeDimensions.length && mean('before') !== document.maturity.compositeBefore) failures.push('compositeBefore is not the rounded mean');
  if (safeDimensions.length && mean('after') !== document.maturity.compositeAfter) failures.push('compositeAfter is not the rounded mean');
  if (failures.length) throw new Error(failures.join('\n'));
}

const escapeMarkdown = text => String(text).replaceAll('|', '\\|');
const escapeXml = text => String(text).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');

export function renderMarkdown(document) {
  const remaining = document.programme.rankedQueue - document.programme.completed;
  const sections = document.projects.map(project => `## ${project.title} · ${project.version}

**Research question.** ${project.question}

**Generated result.** ${project.result}

**Boundary of inference.** ${project.boundary}

[Repository](${project.repositoryUrl}) · [Versioned release](${project.releaseUrl}) · [Live evidence](${project.liveUrl}) · source \`${project.sourceRef}\`
`).join('\n');
  return `# Verified research evidence routed by this profile

This index is generated from [profile-evidence.json](data/profile-evidence.json), pinned to central registry [${document.sourceRegistry.version}](${document.sourceRegistry.url}). It exposes ${document.programme.upstreamEvidenceRecords} upstream evidence records; the programme snapshot is ${document.programme.completed}/${document.programme.rankedQueue} complete with ${remaining} remaining.

> ${document.programme.boundary}

| Project | Release | Question | Result boundary |
| --- | --- | --- | --- |
${document.projects.map(project => `| [${escapeMarkdown(project.title)}](${project.repositoryUrl}) | [${project.version}](${project.releaseUrl}) | ${escapeMarkdown(project.question)} | ${escapeMarkdown(project.boundary)} |`).join('\n')}

${sections}
## Provenance

- Verified: ${document.verifiedDate}
- Profile evidence release: ${document.profileRelease}
- Central registry: [${document.sourceRegistry.version}](${document.sourceRegistry.dataUrl})
- Scope: ${document.maturity.scope}
`;
}

export function renderCsv(document) {
  const rows = ['dimension,before,after,delta'];
  for (const item of document.maturity.dimensions) rows.push(`"${item.name.replaceAll('"', '""')}",${item.before},${item.after},${item.after - item.before}`);
  rows.push(`Composite,${document.maturity.compositeBefore},${document.maturity.compositeAfter},${document.maturity.compositeAfter - document.maturity.compositeBefore}`);
  return `${rows.join('\n')}\n`;
}

export function renderSvg(document) {
  const width = 1200, left = 315, chartWidth = 760, rowHeight = 58, top = 190;
  const height = top + document.maturity.dimensions.length * rowHeight + 112;
  const rows = document.maturity.dimensions.map((item, index) => {
    const y = top + index * rowHeight;
    const beforeWidth = chartWidth * item.before / 100;
    const afterWidth = chartWidth * item.after / 100;
    return `<g><text x="${left - 18}" y="${y + 22}" text-anchor="end" class="label">${escapeXml(item.name)}</text><rect x="${left}" y="${y}" width="${chartWidth}" height="15" rx="7" class="track"/><rect x="${left}" y="${y}" width="${beforeWidth.toFixed(1)}" height="15" rx="7" class="before"/><text x="${left + beforeWidth + 9}" y="${y + 12}" class="value before-text">${item.before}</text><rect x="${left}" y="${y + 23}" width="${chartWidth}" height="15" rx="7" class="track"/><rect x="${left}" y="${y + 23}" width="${afterWidth.toFixed(1)}" height="15" rx="7" class="after"/><text x="${left + afterWidth + 9}" y="${y + 35}" class="value after-text">${item.after}</text></g>`;
  }).join('\n');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="title desc">
  <title id="title">Profile evidence maturity before and after the v1.1 upgrade</title>
  <desc id="desc">Eight paired horizontal bars compare before and after scores. The composite rises from ${document.maturity.compositeBefore} to ${document.maturity.compositeAfter} out of 100. Scores measure auditable research communication, not scientific merit.</desc>
  <style>.bg{fill:#07111f}.title{font:700 34px system-ui,sans-serif;fill:#f8fafc}.subtitle{font:18px system-ui,sans-serif;fill:#a9b8ce}.label{font:600 17px system-ui,sans-serif;fill:#e2e8f0}.value{font:700 14px ui-monospace,monospace}.track{fill:#1b2c42}.before{fill:#64748b}.after{fill:#2dd4bf}.before-text{fill:#cbd5e1}.after-text{fill:#5eead4}.legend{font:600 15px system-ui,sans-serif;fill:#cbd5e1}.note{font:15px system-ui,sans-serif;fill:#94a3b8}</style>
  <rect class="bg" width="${width}" height="${height}" rx="24"/><text x="60" y="62" class="title">Profile evidence maturity · ${document.maturity.compositeBefore} → ${document.maturity.compositeAfter}</text><text x="60" y="96" class="subtitle">Versioned releases, generated findings and inference boundaries replace untraceable profile claims.</text><rect x="60" y="126" width="22" height="12" rx="6" class="before"/><text x="92" y="138" class="legend">Before</text><rect x="176" y="126" width="22" height="12" rx="6" class="after"/><text x="208" y="138" class="legend">After</text><text x="1075" y="138" text-anchor="end" class="note">0–100 documented rubric</text>${rows}<text x="60" y="${height - 40}" class="note">Scope: ${escapeXml(document.maturity.scope)} · ${document.profileRelease}</text></svg>\n`;
}

export function outputs(document) {
  validateEvidence(document);
  return new Map([[MARKDOWN_PATH, renderMarkdown(document)], [CSV_PATH, renderCsv(document)], [SVG_PATH, renderSvg(document)]]);
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
