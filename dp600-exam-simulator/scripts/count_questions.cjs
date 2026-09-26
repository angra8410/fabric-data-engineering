const fs = require('fs');

// In parsed_mslearn_test2.json, it's valid JSON
const msQuestions = JSON.parse(fs.readFileSync('src/data/parsed_mslearn_test2.json', 'utf8'));
console.log('MS Learn Questions count:', msQuestions.length);

// In dp600Questions.ts:
// Let's count top-level objects in STARTER_QUESTIONS
const dpText = fs.readFileSync('src/data/dp600Questions.ts', 'utf8');
// Each question has type: 'multiple_choice' or 'multi_select' or 'drag_and_drop'
const types = [...dpText.matchAll(/type:\s*['"](multiple_choice|multi_select|drag_and_drop)['"]/g)];
console.log('STARTER_QUESTIONS count by type:', types.length);

const dpQIds = [...dpText.matchAll(/^\s+id:\s*['"]([^'"]+)['"],/gm)].map(m => m[1]);
console.log('STARTER_QUESTIONS top-level IDs:', dpQIds.length);
console.log('Sample top-level IDs:', dpQIds.slice(0, 5));

const msQIds = msQuestions.map(q => q.id);
console.log('MS Learn IDs:', msQIds.slice(0, 5));

const setMs = new Set(msQIds);
const inBoth = dpQIds.filter(id => setMs.has(id));
console.log('IDs in both:', inBoth.length, inBoth);

console.log('Total unique questions:', dpQIds.length + msQuestions.length - inBoth.length);
