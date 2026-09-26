const fs = require('fs');
const path = require('path');

const tsContent = fs.readFileSync(path.join(__dirname, '../src/data/mslearnQuestions.ts'), 'utf8');
const newQuestions = JSON.parse(fs.readFileSync(path.join(__dirname, '../src/data/parsed_mslearn_test2.json'), 'utf8'));

// Extract texts from previous mslearnQuestions.ts
const prevTexts = [];
const textMatches = tsContent.matchAll(/"text":\s*"([^"]+)"/g);
for (const m of textMatches) {
  prevTexts.push(m[1].replace(/\\n/g, '\n').trim().toLowerCase());
}

console.log(`Previous questions in mslearnQuestions.ts: ~${prevTexts.length}`);
console.log(`New questions: ${newQuestions.length}`);

let overlap = 0;
newQuestions.forEach(nq => {
  const norm = nq.text.trim().toLowerCase();
  const found = prevTexts.some(pt => pt.includes(norm.substring(0, 40)) || norm.includes(pt.substring(0, 40)));
  if (found) overlap++;
});

console.log(`Overlap between old and new: ${overlap} / ${newQuestions.length}`);
