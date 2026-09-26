export type DomainId = 'domain1' | 'domain2' | 'domain3';

export interface DomainInfo {
  id: DomainId;
  code: string;
  name: string;
  percentage: string;
  minWeight: number;
  maxWeight: number;
  description: string;
  keyTopics: string[];
}

export const DOMAINS: Record<DomainId, DomainInfo> = {
  domain1: {
    id: 'domain1',
    code: 'Domain 1',
    name: 'Plan, implement, and manage an analytics solution',
    percentage: '10–15%',
    minWeight: 0.10,
    maxWeight: 0.15,
    description: 'Workspaces, Fabric capacities, governance, security, deployment pipelines, and Git integration.',
    keyTopics: ['Capacity & Workspace Admin', 'Deployment Pipelines & Git', 'OneLake Security & Governance', 'Monitoring & Tenant Settings']
  },
  domain2: {
    id: 'domain2',
    code: 'Domain 2',
    name: 'Prepare and connect to data',
    percentage: '40–45%',
    minWeight: 0.40,
    maxWeight: 0.45,
    description: 'OneLake shortcuts, Delta Lake optimization, Lakehouse vs. Warehouse, PySpark, T-SQL, and Dataflows Gen2.',
    keyTopics: ['OneLake Shortcuts', 'Delta Lake (V-Order, OPTIMIZE, VACUUM)', 'Lakehouse vs Warehouse', 'PySpark Transformations', 'Dataflows Gen2 & Pipelines']
  },
  domain3: {
    id: 'domain3',
    code: 'Domain 3',
    name: 'Model and explore data',
    percentage: '40–45%',
    minWeight: 0.40,
    maxWeight: 0.45,
    description: 'Semantic models, Direct Lake mode, DAX calculations, Calculation Groups, performance tuning, and KQL.',
    keyTopics: ['Direct Lake Requirements & Fallback', 'Tabular Modeling & DAX', 'Calculation Groups & Field Parameters', 'DAX Studio & Performance Tuning', 'Real-Time Intelligence (KQL)']
  }
};

export type QuestionType = 'multiple_choice' | 'multi_select' | 'drag_and_drop';

export interface QuestionOption {
  id: string; // 'A', 'B', 'C', 'D', 'E', ...
  text: string;
}

export interface OrderingStep {
  id: string;
  text: string;
}

export interface Question {
  id: string;
  type?: QuestionType;
  text: string;
  codeSnippet?: {
    language: 'dax' | 'python' | 'sql' | 'kql' | 'json';
    code: string;
  };
  options: QuestionOption[];
  correctOptionId: string; // 'A' | 'B' | ... (for single-select or primary)
  correctOptionIds?: string[] | null; // ['A', 'C', 'D'] for multi-select
  selectCount?: number | null; // Number of options to select, e.g. 2 or 3
  orderingSteps?: OrderingStep[]; // for drag & drop questions
  correctOrder?: string[]; // IDs in correct 1-to-N order
  domain: DomainId;
  topic: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  explanation: string;
  distractorExplanations?: Record<string, string>;
  msLearnUrl?: string;
  msLearnTitle?: string;
  caseStudyId?: string;
  isCustom?: boolean;
}

export interface CaseStudy {
  id: string;
  title: string;
  overview: string;
  currentEnvironment: string[];
  businessRequirements: string[];
  technicalConstraints: string[];
  identifiedIssues: string[];
}

export interface ExamAttempt {
  id: string;
  timestamp: string;
  score: number; // 0 - 1000
  passed: boolean;
  totalQuestions: number;
  correctCount: number;
  timeSpentSeconds: number;
  domainScores: Record<DomainId, {
    total: number;
    correct: number;
    percentage: number;
  }>;
  userAnswers: Record<string, string>; // questionId -> optionId
  flaggedQuestionIds: string[];
  questionIds: string[];
  weakTopics: string[];
}

export interface UserStats {
  streakDays: number;
  lastStudyDate: string;
  totalAnswered: number;
  correctAnswers: number;
  answeredQuestionIds: Record<string, { 
    answeredOptionId: string; 
    isCorrect: boolean; 
    lastAttemptDate: string;
    attemptCount?: number;
    correctCount?: number;
  }>;
  bookmarkedQuestionIds: string[];
  examAttempts: ExamAttempt[];
  customQuestions: Question[];
}

export interface CheatSheet {
  id: string;
  title: string;
  badge: string;
  domain: DomainId;
  summary: string;
  comparisonTable?: {
    headers: string[];
    rows: { label: string; values: string[] }[];
  };
  keyRules: string[];
  commonTrap: string;
  msLearnRef: {
    title: string;
    url: string;
  };
}
