import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { loadEvidence, outputs, ROOT, validateEvidence } from '../scripts/build_evidence_index.mjs';

test('committed profile evidence satisfies the schema contract', () => {
  const document = loadEvidence();
  assert.doesNotThrow(() => validateEvidence(document));
  assert.equal(document.projects.length, 7);
  assert.equal(document.evidenceIndex.upstreamEvidenceRecords, 7);
});

test('generated Markdown, CSV and SVG are current', () => {
  for (const [file, content] of outputs(loadEvidence())) assert.equal(fs.readFileSync(file, 'utf8'), content, path.relative(ROOT, file));
});

test('every routed record has one matching versioned release', () => {
  const projects = loadEvidence().projects;
  assert.equal(new Set(projects.map(project => project.slug)).size, projects.length);
  for (const project of projects) {
    assert.ok(project.releaseUrl.endsWith(`/releases/tag/${project.version}`));
    assert.match(project.sourceRef, /^[A-Za-z0-9.]{7,}$/);
  }
});

test('claim boundaries reject over-interpretation', () => {
  for (const project of loadEvidence().projects) {
    assert.ok(project.boundary.length >= 60);
    assert.match(project.boundary.toLowerCase(), /not|boundary|diagnostic|experiment|sensitivity|registry/);
  }
});

test('profile cover links the cinematic radar and keeps research provenance in the dedicated index', () => {
  const readme = fs.readFileSync(path.join(ROOT, 'README.md'), 'utf8');
  const index = fs.readFileSync(path.join(ROOT, 'EVIDENCE.md'), 'utf8');
  assert.match(readme, /assets\\/profile-cinema\\/research-radar-cinematic\\.gif/);
  for (const project of loadEvidence().projects) {
    assert.ok(index.includes(project.releaseUrl), project.slug);
  }
});
