const fs = require('fs');
const path = require('path');

const questions = JSON.parse(fs.readFileSync(path.join(__dirname, '../src/data/parsed_mslearn_test2.json'), 'utf8'));

questions.forEach((q, idx) => {
  console.log(`Q${idx + 1}: ${q.options.length} options`);
});
