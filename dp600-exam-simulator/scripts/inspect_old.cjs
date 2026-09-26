const fs = require('fs');
const path = require('path');

const ts = fs.readFileSync(path.join(__dirname, '../src/data/mslearnQuestions.ts'), 'utf8');

// Strip "import..." and "export const MS_LEARN_50_QUESTIONS: Question[] = "
const jsonPart = ts.substring(ts.indexOf('['), ts.lastIndexOf(']') + 1);

try {
  const oldQuestions = JSON.parse(jsonPart);
  console.log(`Successfully parsed ${oldQuestions.length} existing questions in mslearnQuestions.ts`);

  const newQuestions = JSON.parse(fs.readFileSync(path.join(__dirname, '../src/data/parsed_mslearn_test2.json'), 'utf8'));

  // Count how many had dummy fallbacks in old questions
  let dummyCount = 0;
  oldQuestions.forEach(q => {
    const hasDummy = q.options?.some(opt => 
      opt.text.includes('Use workspace Viewer role') || 
      opt.text.includes('Use DirectQuery mode pointing to SQL analytics') ||
      opt.text.includes('COUNT; MEAN') ||
      opt.text.includes('Configure an Azure Data Factory pipeline with copy')
    );
    if (hasDummy) dummyCount++;
  });
  console.log(`Old questions with dummy fallbacks: ${dummyCount} / ${oldQuestions.length}`);

} catch (err) {
  console.error('Failed to parse old questions:', err.message);
}
