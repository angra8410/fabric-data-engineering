with open('mslearn_dp600_50q.json', 'r', encoding='utf-8') as f:
    data = f.read()

with open('src/data/mslearnQuestions.ts', 'w', encoding='utf-8') as f:
    f.write('import { Question } from "../types";\n\nexport const MS_LEARN_50_QUESTIONS: Question[] = ' + data + ';\n')

print('Exported to src/data/mslearnQuestions.ts')
