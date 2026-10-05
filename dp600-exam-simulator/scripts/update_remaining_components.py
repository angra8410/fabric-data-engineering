with open('src/components/PracticeMode.tsx', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("import { Question, DomainId, DOMAINS, UserStats } from '../types';", "import { Question, DomainId, UserStats, ExamId, getDomainsForExam } from '../types';")
text = text.replace("interface PracticeModeProps {", "interface PracticeModeProps {\n  activeExam?: ExamId;")
text = text.replace("  initialQuestionId\n}) => {", "  initialQuestionId,\n  activeExam = 'dp700'\n}) => {\n  const examDomains = getDomainsForExam(activeExam);")
text = text.replace("DOMAINS[currentQuestion.domain]", "examDomains[currentQuestion.domain]")
text = text.replace("DOMAINS[domain].name", "examDomains[domain].name")
text = text.replace("DOMAINS[domain].code", "examDomains[domain].code")
with open('src/components/PracticeMode.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

with open('src/components/QuestionBank.tsx', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("import { Question, DomainId, DOMAINS, UserStats } from '../types';", "import { Question, DomainId, UserStats, ExamId, getDomainsForExam } from '../types';")
text = text.replace("interface QuestionBankProps {", "interface QuestionBankProps {\n  activeExam?: ExamId;")
text = text.replace("  onStatsChange\n}) => {", "  onStatsChange,\n  activeExam = 'dp700'\n}) => {\n  const examDomains = getDomainsForExam(activeExam);")
text = text.replace("DOMAINS[q.domain]", "examDomains[q.domain]")
text = text.replace("DOMAINS[domain].name", "examDomains[domain].name")
text = text.replace("DOMAINS[domain].code", "examDomains[domain].code")
with open('src/components/QuestionBank.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

with open('src/components/MistakeReview.tsx', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("import { Question, UserStats, DOMAINS } from '../types';", "import { Question, UserStats, ExamId, getDomainsForExam } from '../types';")
text = text.replace("interface MistakeReviewProps {", "interface MistakeReviewProps {\n  activeExam?: ExamId;")
text = text.replace("  onStartPractice\n}) => {", "  onStartPractice,\n  activeExam = 'dp700'\n}) => {\n  const examDomains = getDomainsForExam(activeExam);")
text = text.replace("DOMAINS[q.domain]", "examDomains[q.domain]")
with open('src/components/MistakeReview.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

with open('src/components/PerformanceAnalytics.tsx', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("import { UserStats, Question, DOMAINS, DomainId } from '../types';", "import { UserStats, Question, DomainId, ExamId, getDomainsForExam } from '../types';")
text = text.replace("interface PerformanceAnalyticsProps {", "interface PerformanceAnalyticsProps {\n  activeExam?: ExamId;")
text = text.replace("  onStartExam\n}) => {", "  onStartExam,\n  activeExam = 'dp700'\n}) => {\n  const examDomains = getDomainsForExam(activeExam);")
text = text.replace("info: DOMAINS[dId]", "info: examDomains[dId]")
with open('src/components/PerformanceAnalytics.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

with open('src/components/StarredQuestions.tsx', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("import { Question, UserStats, DOMAINS } from '../types';", "import { Question, UserStats, ExamId, getDomainsForExam } from '../types';")
text = text.replace("interface StarredQuestionsProps {", "interface StarredQuestionsProps {\n  activeExam?: ExamId;")
text = text.replace("  onStatsChange\n}) => {", "  onStatsChange,\n  activeExam = 'dp700'\n}) => {\n  const examDomains = getDomainsForExam(activeExam);")
text = text.replace("DOMAINS[q.domain]", "examDomains[q.domain]")
with open('src/components/StarredQuestions.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated PracticeMode, QuestionBank, MistakeReview, PerformanceAnalytics, StarredQuestions successfully!')
