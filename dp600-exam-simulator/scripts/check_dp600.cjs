const fs = require('fs');
const content = fs.readFileSync('src/data/dp600Questions.ts', 'utf8');
const idMatches = content.match(/id:\s*'[^']+'/g) || [];
const questionIds = idMatches.filter(id => {
  return !/id:\s*'[A-F]'/.test(id) && !/id:\s*'step-/.test(id);
});
console.log('Question-like IDs in dp600Questions.ts (Count = ' + questionIds.length + '):');
console.log(questionIds);
