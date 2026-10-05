with open('src/components/ExamResults.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Update imports
text = text.replace("import { ExamAttempt, Question, DOMAINS, DomainId } from '../types';", "import { ExamAttempt, Question, DomainId, ExamId, getDomainsForExam } from '../types';")

# Update props
old_props = '''interface ExamResultsProps {
  attempt: ExamAttempt;
  questions: Question[];
  setActiveTab: (tab: ActiveTab) => void;
  onRetakeExam: () => void;
  onDrillWeakTopic: (topic: string) => void;
}'''

new_props = '''interface ExamResultsProps {
  attempt: ExamAttempt;
  questions: Question[];
  activeExam?: ExamId;
  setActiveTab: (tab: ActiveTab) => void;
  onRetakeExam: () => void;
  onDrillWeakTopic: (topic: string) => void;
}'''
text = text.replace(old_props, new_props)

old_comp = '''export const ExamResults: React.FC<ExamResultsProps> = ({
  attempt,
  questions,
  setActiveTab,
  onRetakeExam,
  onDrillWeakTopic
}) => {'''

new_comp = '''export const ExamResults: React.FC<ExamResultsProps> = ({
  attempt,
  questions,
  activeExam = 'dp700',
  setActiveTab,
  onRetakeExam,
  onDrillWeakTopic
}) => {
  const examDomains = getDomainsForExam(attempt.examId || activeExam);'''
text = text.replace(old_comp, new_comp)

# Replace DOMAINS references
text = text.replace('const info = DOMAINS[domId];', 'const info = examDomains[domId];')
text = text.replace('{DOMAINS[q.domain].code}', '{examDomains[q.domain]?.code || q.domain}')

with open('src/components/ExamResults.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated ExamResults.tsx successfully')
