const fs = require('fs');
const path = require('path');

const jsonPath = path.join(__dirname, '..', 'src', 'data', 'parsed_mslearn_test2.json');
const targetPath = path.join(__dirname, '..', 'src', 'data', 'mslearnQuestions.ts');

const questions = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
console.log('Total questions from parsed JSON:', questions.length);

const tsContent = `import { Question } from '../types';

export const MS_LEARN_50_QUESTIONS: Question[] = ${JSON.stringify(questions, null, 2)};
`;

fs.writeFileSync(targetPath, tsContent, 'utf8');
console.log('Successfully written to', targetPath);
