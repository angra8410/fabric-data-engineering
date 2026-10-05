with open('src/components/MockExam.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Update imports
text = text.replace("import { Question, ExamAttempt } from '../types';", "import { Question, ExamAttempt, ExamId, getDomainsForExam, EXAMS } from '../types';")

# Update props
old_props = '''interface MockExamProps {
  questions: Question[];
  onFinishExam: (attempt: ExamAttempt) => void;
  onExitExam: () => void;
}'''

new_props = '''interface MockExamProps {
  questions: Question[];
  activeExam?: ExamId;
  onFinishExam: (attempt: ExamAttempt) => void;
  onExitExam: () => void;
}'''
text = text.replace(old_props, new_props)

old_comp = '''export const MockExam: React.FC<MockExamProps> = ({
  questions,
  onFinishExam,
  onExitExam
}) => {'''

new_comp = '''export const MockExam: React.FC<MockExamProps> = ({
  questions,
  activeExam = 'dp700',
  onFinishExam,
  onExitExam
}) => {
  const examInfo = EXAMS[activeExam];'''
text = text.replace(old_comp, new_comp)

# Update submit logic
old_submit = '''  const handleSubmitExam = () => {
    const timeSpent = (selectedDuration * 60) - timeLeftSeconds;
    const attempt = calculateExamScore(examQuestions, userAnswers, timeSpent, flaggedIds);
    storageService.saveExamAttempt(attempt);
    onFinishExam(attempt);
  };'''

new_submit = '''  const handleSubmitExam = () => {
    const timeSpent = (selectedDuration * 60) - timeLeftSeconds;
    const attempt = calculateExamScore(examQuestions, userAnswers, timeSpent, flaggedIds, getDomainsForExam(activeExam));
    attempt.examId = activeExam;
    storageService.saveExamAttempt(attempt, activeExam);
    onFinishExam(attempt);
  };'''
text = text.replace(old_submit, new_submit)

with open('src/components/MockExam.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated MockExam.tsx successfully')
