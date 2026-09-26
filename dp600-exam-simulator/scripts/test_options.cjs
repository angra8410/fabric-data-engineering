const fs = require('fs');
const path = require('path');

const raw = fs.readFileSync(path.join(__dirname, '../src/data/raw_mslearn_test2.txt'), 'utf8');
const text = raw.replace(/\r\n/g, '\n');
const questionBlocks = text.split(/(?=Question \d+ of 50)/g).filter(b => b.trim().length > 0);

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

questionBlocks.forEach((block, idx) => {
  const qNumMatch = block.match(/Question (\d+) of 50/);
  const qNum = qNumMatch ? parseInt(qNumMatch[1]) : idx + 1;

  const selectMatch = block.match(/Select (only one answer|all answers that apply)\./);
  const afterSelect = block.substring(selectMatch.index + selectMatch[0].length).trim();

  let expIndex = -1;
  for (const starter of EXPLANATION_STARTERS) {
    const pos = afterSelect.indexOf(starter);
    if (pos !== -1) {
      if (expIndex === -1 || pos < expIndex) {
        expIndex = pos;
      }
    }
  }

  const optionsRaw = expIndex !== -1 ? afterSelect.substring(0, expIndex).trim() : afterSelect;

  // Let's print optionsRaw for special questions like 6, 14, 32, 37
  if ([1, 2, 6, 14, 27, 32, 36, 37, 41, 42].includes(qNum)) {
    console.log(`=== Q${qNum} OPTIONS RAW ===`);
    console.log(optionsRaw);
    console.log(`============================\n`);
  }
});
