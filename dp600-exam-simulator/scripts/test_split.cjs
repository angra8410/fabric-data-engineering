const fs = require('fs');
const path = require('path');

const raw = fs.readFileSync(path.join(__dirname, '../src/data/raw_mslearn_test2.txt'), 'utf8');
const text = raw.replace(/\r\n/g, '\n');
const questionBlocks = text.split(/(?=Question \d+ of 50)/g).filter(b => b.trim().length > 0);

// Specific explanation start markers or heuristics
const EXPLANATION_STARTERS = [
  "TREATAS() applies the result",
  "Direct Lake storage mode provides",
  "While you can use bookmarks",
  "Dynamic measure formatting is the simplest",
  "The large semantic model storage format",
  "In this example, the Date dimension",
  "Type 0 SCD attributes never change",
  "Objective:",
  "Adding apply buttons will pause",
  "Only Best Practices Analyzer",
  "The ideal file size for Fabric engines",
  "The high concurrency mode for Fabric",
  "Declaring the [Variance] measure",
  "For the Copy Data Activity",
  "You can query data across Fabric",
  "Dataflow Gen2 is a low code",
  "When ingesting a large data source",
  "Scheduling on the external datasource",
  "The Copy data activity should be used",
  "Appending data for the query will add",
  "The display PySpark method is used",
  "The method to add new columns",
  "A left anti join ensures",
  "To load data to a pandas DataFrame",
  "GroupBy will group the data",
  "describe is used to generate descriptive",
  "Split Column is the only applied step",
  "A view provides a convenient way",
  "The Conditional column option enables",
  "When ingesting data by using Dataflow",
  "The GroupBY columns must match",
  "DENSE_RANK() function returns",
  "To create a report showing total sales",
  "Using T-SQL to grant permissions",
  "Since the user only needs access",
  "During the shortcut setup process",
  "Applying sensitivity labels is essential",
  "Implementing row-level security is crucial",
  "Saving your Power BI work as a PBIP",
  "Adding a parameter to filter the data",
  "The data lineage view provides visibility",
  "To enable write operations on semantic",
  "You should select Impact analysis"
];

const results = [];

questionBlocks.forEach((block, idx) => {
  const qNumMatch = block.match(/Question (\d+) of 50/);
  const qNum = qNumMatch ? parseInt(qNumMatch[1]) : idx + 1;

  const selectMatch = block.match(/Select (only one answer|all answers that apply)\./);
  const promptPart = block.substring(0, selectMatch.index).replace(/Question \d+ of 50\s*/, '').trim();
  const isMultiSelect = selectMatch[1] === 'all answers that apply';
  
  let selectCount = null;
  if (isMultiSelect) {
    if (/Which two/i.test(promptPart)) selectCount = 2;
    else if (/Which three/i.test(promptPart)) selectCount = 3;
    else if (/Which four/i.test(promptPart)) selectCount = 4;
  }

  const afterSelect = block.substring(selectMatch.index + selectMatch[0].length).trim();

  // Find where explanation starts
  let expIndex = -1;
  for (const starter of EXPLANATION_STARTERS) {
    const pos = afterSelect.indexOf(starter);
    if (pos !== -1) {
      if (expIndex === -1 || pos < expIndex) {
        expIndex = pos;
      }
    }
  }

  let optionsRaw = '';
  let explanationRaw = '';

  if (expIndex !== -1) {
    optionsRaw = afterSelect.substring(0, expIndex).trim();
    explanationRaw = afterSelect.substring(expIndex).trim();
  } else {
    optionsRaw = afterSelect;
  }

  // Remove "what is the meaning of TRUNCATED data?" if appended at end of Q21
  explanationRaw = explanationRaw.replace(/what is the meaning of TRUNCATED data\?/gi, '').trim();

  results.push({
    qNum,
    prompt: promptPart,
    isMultiSelect,
    selectCount,
    optionsRaw,
    explanationRaw: explanationRaw.substring(0, 150) + '...'
  });
});

results.forEach(r => {
  console.log(`Q${r.qNum}: isMulti=${r.isMultiSelect} (selectCount=${r.selectCount})`);
  console.log(`  Prompt: ${r.prompt.substring(0, 60)}...`);
  console.log(`  Options raw length: ${r.optionsRaw.length}, Expl: ${r.explanationRaw}`);
});
