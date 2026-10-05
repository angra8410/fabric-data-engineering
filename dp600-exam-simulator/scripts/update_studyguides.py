import re

with open('src/components/StudyGuides.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Update imports
text = text.replace("import { DOMAINS, DomainId } from '../types';", "import { DomainId, ExamId, EXAMS, getDomainsForExam } from '../types';")

# Update props
old_props = '''interface StudyGuidesProps {
  onPracticeDomain: (domain: DomainId) => void;
  initialDomainFilter?: DomainId | 'all';
}'''

new_props = '''interface StudyGuidesProps {
  onPracticeDomain: (domain: DomainId) => void;
  initialDomainFilter?: DomainId | 'all';
  activeExam?: ExamId;
}'''
text = text.replace(old_props, new_props)

old_comp = '''export const StudyGuides: React.FC<StudyGuidesProps> = ({ 
  onPracticeDomain,
  initialDomainFilter = 'all'
}) => {'''

new_comp = '''export const StudyGuides: React.FC<StudyGuidesProps> = ({ 
  onPracticeDomain,
  initialDomainFilter = 'all',
  activeExam = 'dp700'
}) => {
  const examInfo = EXAMS[activeExam];
  const examDomains = examInfo.domains;'''
text = text.replace(old_comp, new_comp)

# Filter sheets by examId
old_filtered = '''  // Domain counts
  const domainCounts = useMemo(() => {
    return {
      all: FABRIC_CHEAT_SHEETS.length,
      domain1: FABRIC_CHEAT_SHEETS.filter(s => s.domain === 'domain1').length,
      domain2: FABRIC_CHEAT_SHEETS.filter(s => s.domain === 'domain2').length,
      domain3: FABRIC_CHEAT_SHEETS.filter(s => s.domain === 'domain3').length,
    };
  }, []);

  // Filtered sheets
  const filteredSheets = useMemo(() => {
    return FABRIC_CHEAT_SHEETS.filter(sheet => {
      if (selectedDomain !== 'all' && sheet.domain !== selectedDomain) return false;'''

new_filtered = '''  // Base sheets for current exam
  const relevantSheets = useMemo(() => {
    return FABRIC_CHEAT_SHEETS.filter(s => !s.examId || s.examId === 'all' || s.examId === activeExam);
  }, [activeExam]);

  // Domain counts
  const domainCounts = useMemo(() => {
    return {
      all: relevantSheets.length,
      domain1: relevantSheets.filter(s => s.domain === 'domain1').length,
      domain2: relevantSheets.filter(s => s.domain === 'domain2').length,
      domain3: relevantSheets.filter(s => s.domain === 'domain3').length,
    };
  }, [relevantSheets]);

  // Filtered sheets
  const filteredSheets = useMemo(() => {
    return relevantSheets.filter(sheet => {
      if (selectedDomain !== 'all' && sheet.domain !== selectedDomain) return false;'''

text = text.replace(old_filtered, new_filtered)

# Replace DOMAINS references in StudyGuides with examDomains
text = text.replace('DOMAINS[domain].name', 'examDomains[domain].name')
text = text.replace('DOMAINS[domain].code', 'examDomains[domain].code')
text = text.replace('DOMAINS.domain1.name', 'examDomains.domain1.name')
text = text.replace('DOMAINS.domain2.name', 'examDomains.domain2.name')
text = text.replace('DOMAINS.domain3.name', 'examDomains.domain3.name')
text = text.replace('DP-600 Study Guides', '{examInfo.code} Study Guides')

with open('src/components/StudyGuides.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated StudyGuides.tsx with multi-exam cheat sheets and dynamic domains!')
