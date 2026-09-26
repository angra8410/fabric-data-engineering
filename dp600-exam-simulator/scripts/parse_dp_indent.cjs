const fs = require('fs');

const dp = fs.readFileSync('src/data/dp600Questions.ts', 'utf8');
const lines = dp.split('\n');

const qIndices = [];
for (let i = 0; i < lines.length; i++) {
  if (lines[i].match(/^\s+id:\s*['"]([^'"]+)['"],/)) {
    const id = lines[i].match(/^\s+id:\s*['"]([^'"]+)['"],/)[1];
    // check if it's inside options or steps
    // options are indented more (e.g. 6 or 8 spaces), top level is 4 spaces
    const indent = lines[i].search(/\S/);
    qIndices.push({ line: i + 1, indent, id });
  }
}

console.log('Found question ID lines:');
qIndices.forEach(q => console.log(`Line ${q.line} (indent ${q.indent}): ${q.id}`));

const topLevel = qIndices.filter(q => q.indent === 4);
console.log('\nTop-level questions count:', topLevel.length);
topLevel.forEach(q => console.log(' - ' + q.id));
