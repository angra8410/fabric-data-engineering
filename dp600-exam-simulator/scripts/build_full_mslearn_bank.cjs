const fs = require('fs');
const path = require('path');

const raw = fs.readFileSync(path.join(__dirname, '../src/data/raw_mslearn_test2.txt'), 'utf8');
const text = raw.replace(/\r\n/g, '\n');
const questionBlocks = text.split(/(?=Question \d+ of 50)/g).filter(b => b.trim().length > 0);

// Specific explanation start markers
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

function getDomainAndTopic(qNum, prompt) {
  if ([1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 14, 37].includes(qNum)) {
    if (qNum === 37) return { domain: 'domain3', topic: 'Real-Time Intelligence & KQL' };
    if ([2, 8].includes(qNum)) return { domain: 'domain3', topic: 'Direct Lake Storage Mode' };
    if ([1, 4, 6, 14].includes(qNum)) return { domain: 'domain3', topic: 'DAX Calculations & Measures' };
    if (qNum === 3) return { domain: 'domain3', topic: 'Field Parameters' };
    if ([5, 11].includes(qNum)) return { domain: 'domain3', topic: 'Semantic Model Optimization' };
    if (qNum === 9) return { domain: 'domain3', topic: 'DirectQuery Performance' };
    if (qNum === 10) return { domain: 'domain3', topic: 'Tabular Editor & Best Practice Analyzer' };
    return { domain: 'domain3', topic: 'Model and Explore Data' };
  }

  if ([7, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 40].includes(qNum)) {
    if ([12].includes(qNum)) return { domain: 'domain2', topic: 'Delta Lake (OPTIMIZE & VACUUM)' };
    if ([13, 22, 23, 25, 26, 27].includes(qNum)) return { domain: 'domain2', topic: 'PySpark & Notebooks' };
    if ([15, 17, 18, 19, 20].includes(qNum)) return { domain: 'domain2', topic: 'Data Ingestion & Pipelines' };
    if ([21, 24, 28, 30, 31, 35, 36].includes(qNum)) return { domain: 'domain2', topic: 'Dataflows Gen2 & Power Query' };
    if ([16, 29, 32, 33, 34].includes(qNum)) return { domain: 'domain2', topic: 'Fabric Warehouse & T-SQL' };
    if (qNum === 40) return { domain: 'domain2', topic: 'OneLake Shortcuts' };
    if (qNum === 7) return { domain: 'domain2', topic: 'Dimensional Modeling (SCD)' };
    return { domain: 'domain2', topic: 'Prepare and Connect to Data' };
  }

  if ([38, 39, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50].includes(qNum)) {
    if ([38, 39, 41, 42].includes(qNum)) return { domain: 'domain1', topic: 'Security & Access Control (RLS/DDM)' };
    if ([43, 47].includes(qNum)) return { domain: 'domain1', topic: 'Source Control & Git Integration' };
    if ([44].includes(qNum)) return { domain: 'domain1', topic: 'Deployment Pipelines & ALM' };
    if ([45].includes(qNum)) return { domain: 'domain1', topic: 'Reusable Assets (PBIDS/PBIP)' };
    if ([46, 49].includes(qNum)) return { domain: 'domain1', topic: 'XMLA Endpoint Management' };
    if ([48, 50].includes(qNum)) return { domain: 'domain1', topic: 'Lineage & Impact Analysis' };
    return { domain: 'domain1', topic: 'Plan, Implement & Manage' };
  }

  return { domain: 'domain2', topic: 'Fabric Analytics' };
}

const parsedQuestions = [];

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

  let expIndex = -1;
  for (const starter of EXPLANATION_STARTERS) {
    const pos = afterSelect.indexOf(starter);
    if (pos !== -1) {
      if (expIndex === -1 || pos < expIndex) {
        expIndex = pos;
      }
    }
  }

  let optionsRaw = expIndex !== -1 ? afterSelect.substring(0, expIndex).trim() : afterSelect;
  let explanationRaw = expIndex !== -1 ? afterSelect.substring(expIndex).trim() : '';

  explanationRaw = explanationRaw.replace(/what is the meaning of TRUNCATED data\?/gi, '').trim();

  let msLearnUrl = 'https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/';
  const urlMatch = explanationRaw.match(/https?:\/\/[^\s\)]+/);
  if (urlMatch) {
    msLearnUrl = urlMatch[0];
  }

  let options = [];
  let correctOptionIds = [];

  // Special handling for code-heavy questions
  if (qNum === 6) {
    options = [
      {
        id: 'A',
        text: `Sales Shipped =\nCALCULATE (\n    SUM ( 'Sales'[SalesAmount] ),\n    RELATED ( 'Date'[DateKey], 'Sales'[ShipDateKey] )\n)\n\nSales Ordered =\nCALCULATE (\n    SUM ( 'Sales'[SalesAmount] ),\n    RELATED ( 'Date'[DateKey], 'Sales'[OrderDateKey] )\n)`
      },
      {
        id: 'B',
        text: `Sales Shipped =\nCALCULATE (\n    SUM ( 'Sales'[SalesAmount] ),\n    USERELATIONSHIP ( 'Date'[DateKey], 'Sales'[ShipDateKey] )\n)\n\nSales Ordered =\nSUM ( 'Sales'[SalesAmount] )`
      },
      {
        id: 'C',
        text: `Sales Shipped =\nCALCULATE (\n    SUM ( 'Sales'[SalesAmount] ),\n    RELATED ( 'Date'[DateKey], 'Sales'[ShipDateKey] )\n)\n\nSales Ordered =\nCALCULATE (\n    SUM ( 'Sales'[SalesAmount] ),\n    RELATED ( 'Date'[DateKey], 'Sales'[OrderDateKey] )\n)`
      },
      {
        id: 'D',
        text: `Sales Ordered =\nSUM ( 'Sales'[SalesAmount] )\n\nSales Shipped =\nCALCULATE (\n    SUM ( 'Sales'[SalesAmount] ),\n    USERELATIONSHIP ( 'Date'[DateKey], 'Sales'[ShipDateKey] )\n)`
      }
    ];
    correctOptionIds = ['D'];
  } else if (qNum === 14) {
    options = [
      {
        id: 'A',
        text: `SWITCH( TRUE(),\n    [Variance] > 0.80, "Amazing!",\n    [Variance] > 0.60, "Good",\n    "Bad"\n)`
      },
      {
        id: 'B',
        text: `VAR Calc = [Variance]\nRETURN\nSWITCH(TRUE(),\n    Calc > 0.80, "Amazing!",\n    Calc > 0.60, "Good",\n    "Bad"\n)`
      },
      {
        id: 'C',
        text: `VAR Calc = [Variance]\nRETURN\nSWITCH( TRUE(),\n    Calc > 0.80, "Amazing!",\n    [Variance] > 0.60, "Good",\n    "Bad"\n)`
      },
      {
        id: 'D',
        text: `VAR Calc = [Variance]\nRETURN\nSWITCH( TRUE(),\n    [Variance] > 0.80, "Amazing!",\n    [Variance] > 0.60, "Good",\n    "Bad"\n)`
      }
    ];
    correctOptionIds = ['B'];
  } else if (qNum === 25) {
    options = [
      {
        id: 'A',
        text: `df = pandas.read_parquet("/lakehouse/default/Files/Customers.parquet")`
      },
      {
        id: 'B',
        text: `df = pandas.read_parquet("/lakehouse/Files/Customers.parquet")`
      },
      {
        id: 'C',
        text: `import pandas as pd\ndf = pd.read_parquet("/lakehouse/default/Files/Customers.parquet")`
      },
      {
        id: 'D',
        text: `import pandas as pd\ndf = pd.read_parquet("/lakehouse/Files/Customers.parquet")`
      }
    ];
    correctOptionIds = ['C'];
  } else if (qNum === 32) {
    options = [
      {
        id: 'A',
        text: `GROUP BY p.ProductKey, d.DateKey\nHAVING SUM(s.SalesAmount) > 10000`
      },
      {
        id: 'B',
        text: `GROUP BY p.ProductName, d.Year\nHAVING SUM(s.SalesAmount) > 10000`
      },
      {
        id: 'C',
        text: `WHERE s.SalesAmount > 10000\nGROUP BY p.ProductKey, d.DateKey`
      },
      {
        id: 'D',
        text: `WHERE s.SalesAmount > 10000\nGROUP BY p.ProductName, d.Year`
      }
    ];
    correctOptionIds = ['B'];
  } else {
    // Standard questions
    let cleanOptionsBlock = optionsRaw
      .replace(/\n\s*This answer is correct\./g, ' [[CORRECT]]')
      .replace(/\n\s*This answer is incorrect\./g, ' [[INCORRECT]]');

    const rawOptionItems = cleanOptionsBlock.split(/\n\s*\n+/).map(o => o.trim()).filter(Boolean);
    const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
    
    rawOptionItems.forEach((item, oIdx) => {
      const optId = letters[oIdx] || `OPT_${oIdx}`;
      const isCorrect = item.includes('[[CORRECT]]');
      const optText = item.replace('[[CORRECT]]', '').replace('[[INCORRECT]]', '').trim();
      
      options.push({
        id: optId,
        text: optText
      });

      if (isCorrect) {
        correctOptionIds.push(optId);
      }
    });
  }

  const { domain, topic } = getDomainAndTopic(qNum, promptPart);

  parsedQuestions.push({
    id: `mslearn-set2-q${String(qNum).padStart(2, '0')}`,
    type: isMultiSelect ? 'multi_select' : 'multiple_choice',
    text: promptPart,
    options,
    correctOptionId: correctOptionIds[0] || 'A',
    correctOptionIds: isMultiSelect ? correctOptionIds : null,
    selectCount: isMultiSelect ? (selectCount || correctOptionIds.length) : null,
    domain,
    topic,
    difficulty: 'Medium',
    explanation: explanationRaw,
    msLearnUrl,
    msLearnTitle: `Microsoft Learn - ${topic}`,
    isCustom: true
  });
});

console.log(`Successfully parsed ${parsedQuestions.length} questions.`);

parsedQuestions.forEach(q => {
  const correct = q.type === 'multi_select' ? q.correctOptionIds.join(',') : q.correctOptionId;
  console.log(`Q ${q.id}: ${q.type} | count=${q.options.length} | correct=${correct}`);
});

fs.writeFileSync(
  path.join(__dirname, '../src/data/parsed_mslearn_test2.json'),
  JSON.stringify(parsedQuestions, null, 2),
  'utf8'
);
