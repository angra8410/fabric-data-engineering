const fs = require('fs');
const path = require('path');

const questions = JSON.parse(fs.readFileSync(path.join(__dirname, '../src/data/parsed_mslearn_test2.json'), 'utf8'));

console.log(`Total questions: ${questions.length}`);

questions.forEach((q, idx) => {
  const optCount = q.options.length;
  const correct = q.type === 'multi_select' ? q.correctOptionIds.join(',') : q.correctOptionId;
  if ([6, 14, 27, 32, 36, 37, 41, 42].includes(idx + 1)) {
    console.log(`\n--- Q${idx + 1} (${q.type}, selectCount=${q.selectCount}, correct=${correct}) ---`);
    console.log(`Text: ${q.text.substring(0, 80)}...`);
    q.options.forEach(o => {
      console.log(`  [${o.id}] ${o.text.substring(0, 60)}...`);
    });
  }
});
