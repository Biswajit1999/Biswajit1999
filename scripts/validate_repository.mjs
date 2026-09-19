import fs from 'node:fs';
import path from 'node:path';
import { outputs, loadEvidence, ROOT } from './build_evidence_index.mjs';

const failures = [];
const document = loadEvidence();
for (const [file, generated] of outputs(document)) {
  if (!fs.existsSync(file)) failures.push(`${path.relative(ROOT, file)} missing`);
  else if (fs.readFileSync(file, 'utf8') !== generated) failures.push(`${path.relative(ROOT, file)} stale`);
}

const readme = fs.readFileSync(path.join(ROOT, 'README.md'), 'utf8');
for (const required of ['Verified Research Evidence', 'EVIDENCE.md', 'profile-evidence-maturity.svg', document.sourceRegistry.version, `${document.programme.completed}/${document.programme.rankedQueue}`, 'discovery-only']) {
  if (!readme.includes(required)) failures.push(`README missing: ${required}`);
}
for (const project of document.projects) {
  if (!readme.includes(project.releaseUrl)) failures.push(`README missing release: ${project.slug}`);
}

if (failures.length) {
  console.error(failures.join('\n'));
  process.exit(1);
}
console.log(`Profile validation passed: ${document.projects.length} evidence records, ${document.maturity.dimensions.length} maturity dimensions.`);
