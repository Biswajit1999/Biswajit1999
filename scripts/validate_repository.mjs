import fs from 'node:fs';
import path from 'node:path';
import { outputs, loadEvidence, ROOT } from './build_evidence_index.mjs';

const failures = [];
const document = loadEvidence();
for (const [file, generated] of outputs(document)) {
  if (!fs.existsSync(file)) failures.push(`${path.relative(ROOT, file)} missing`);
  else if (fs.readFileSync(file, 'utf8') !== generated) failures.push(`${path.relative(ROOT, file)} stale`);
}

// The README is a visual cover, not the registry index. Validate each separately.
const readme = fs.readFileSync(path.join(ROOT, 'README.md'), 'utf8');
const index = fs.readFileSync(path.join(ROOT, 'EVIDENCE.md'), 'utf8');
if (!readme.includes('assets/profile-cinema/research-radar-cinematic.gif')) failures.push('README cinematic cover missing');
if (!index.includes(document.sourceRegistry.version)) failures.push('EVIDENCE.md registry version missing');
for (const project of document.projects) {
  if (!index.includes(project.releaseUrl)) failures.push(`EVIDENCE.md missing release: ${project.slug}`);
}

if (failures.length) {
  console.error(failures.join('\n'));
  process.exit(1);
}
console.log(`Profile validation passed: ${document.projects.length} evidence records.`);
