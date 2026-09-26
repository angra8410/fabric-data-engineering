const fs = require('fs');
const path = require('path');

const raw = fs.readFileSync(path.join(__dirname, '../src/data/raw_mslearn_test2.txt'), 'utf8');

// Normalize line endings
const text = raw.replace(/\r\n/g, '\n');

// Split questions by "Question X of 50"
const questionBlocks = text.split(/(?=Question \d+ of 50)/g).filter(b => b.trim().length > 0);

console.log(`Found ${questionBlocks.length} question blocks.`);

const parsedQuestions = [];

questionBlocks.forEach((block, index) => {
  const qNumMatch = block.match(/Question (\d+) of 50/);
  const qNum = qNumMatch ? parseInt(qNumMatch[1]) : index + 1;

  // Find question prompt
  const selectMatch = block.match(/Select (only one answer|all answers that apply)\./);
  if (!selectMatch) {
    console.error(`Block ${qNum} has no Select match!`);
    return;
  }

  const promptPart = block.substring(0, selectMatch.index).replace(/Question \d+ of 50\s*/, '').trim();
  const isMultiSelect = selectMatch[1] === 'all answers that apply';
  
  let selectCount = null;
  if (isMultiSelect) {
    if (/Which two/i.test(promptPart)) selectCount = 2;
    else if (/Which three/i.test(promptPart)) selectCount = 3;
    else if (/Which four/i.test(promptPart)) selectCount = 4;
  }

  const afterSelect = block.substring(selectMatch.index + selectMatch[0].length).trim();

  parsedQuestions.push({
    qNum,
    prompt: promptPart,
    isMultiSelect,
    selectCount,
    rawBody: afterSelect
  });
});

console.log(`Parsed ${parsedQuestions.length} prompts.`);
