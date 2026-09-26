const fs = require('fs');

// Read STARTER_QUESTIONS from dp600Questions.ts
// Let's use ts-node or just extract using node
const dpText = fs.readFileSync('src/data/dp600Questions.ts', 'utf8');
const msText = fs.readFileSync('src/data/mslearnQuestions.ts', 'utf8');

// Let's find each question object in dp600Questions
// Let's write a tiny bundler or evaluate it by converting export to module.exports
const cleanDp = dpText.replace(/import\s+[^;]+;/g, '').replace(/export\s+const\s+STARTER_QUESTIONS\s*:\s*Question\[\]\s*=/, 'module.exports =');
fs.writeFileSync('scripts/temp_dp.js', cleanDp, 'utf8');
const starterQuestions = require('./temp_dp.js');

const cleanMs = msText.replace(/import\s+[^;]+;/g, '').replace(/export\s+const\s+MS_LEARN_50_QUESTIONS\s*:\s*Question\[\]\s*=/, 'module.exports =');
fs.writeFileSync('scripts/temp_ms.js', cleanMs, 'utf8');
const msQuestions = require('./temp_ms.js');

console.log('starterQuestions length:', starterQuestions.length);
console.log('msQuestions length:', msQuestions.length);

const combined = [...starterQuestions, ...msQuestions];
console.log('combined length:', combined.length);

// Check duplicate IDs
const ids = new Map();
for (const q of combined) {
  if (ids.has(q.id)) {
    console.log('Duplicate ID:', q.id);
  } else {
    ids.set(q.id, q);
  }
}
console.log('Unique IDs count:', ids.size);

// Check duplicate text/content
const textMap = new Map();
const duplicates = [];
for (const q of combined) {
  const norm = q.text.trim().toLowerCase().slice(0, 60);
  if (textMap.has(norm)) {
    duplicates.push({ id1: textMap.get(norm).id, id2: q.id, text: norm });
  } else {
    textMap.set(norm, q);
  }
}
console.log('Duplicate text count:', duplicates.length);
duplicates.forEach(d => console.log(' -', d.id1, 'vs', d.id2, '::', d.text));

