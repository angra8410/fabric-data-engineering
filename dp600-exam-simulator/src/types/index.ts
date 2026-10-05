export type DomainId = 'domain1' | 'domain2' | 'domain3';
export type ExamId = 'dp600' | 'dp700';

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

export interface ExamInfo {
  id: ExamId;
  code: string;
  title: string;
  shortTitle: string;
  badge: string;
  description: string;
  targetRole: string;
  domains: Record<DomainId, DomainInfo>;
}

export const EXAMS: Record<ExamId, ExamInfo> = {
  dp700: {
    id: 'dp700',
    code: 'DP-700',
    title: 'Implementing Data Engineering Solutions Using Microsoft Fabric',
    shortTitle: 'Fabric Data Engineer',
    badge: 'Fabric Data Engineer Associate',
    targetRole: 'Data Engineers & Big Data Architects',
    description: 'Design, implement, and maintain enterprise data engineering solutions using Microsoft Fabric lakehouses, warehouses, real-time intelligence, and pipelines.',
    domains: {
      domain1: {
        id: 'domain1',
        code: 'Domain 1',
        name: 'Implement and manage an analytics solution',
        percentage: '30–35%',
        minWeight: 0.30,
        maxWeight: 0.35,
        description: 'Fabric security (RLS, CLS, DDM, compute permissions), lifecycle management (Git & deployment pipelines), and pipeline orchestration.',
        keyTopics: [
          'Security (RLS, CLS, DDM, Granular SQL Grants)',
          'Git Integration & Recovery (Revert/Sync)',
          'Deployment Pipelines & Selective Promotion',
          'Data Factory Orchestration & Triggers',
          'Data Mesh & Domain Governance Delegation'
        ]
      },
      domain2: {
        id: 'domain2',
        code: 'Domain 2',
        name: 'Ingest and transform data',
        percentage: '40–45%',
        minWeight: 0.40,
        maxWeight: 0.45,
        description: 'Shortcuts, Mirrored Databases, T-SQL COPY/CTAS, SCD Type 2, Eventstreams, KQL databases, and streaming windowing.',
        keyTopics: [
          'OneLake Shortcuts & Mirrored Databases',
          'T-SQL COPY & CTAS Batch Loading',
          'SCD Type 2 Dimensional Modeling',
          'Eventstreams & No-Code Event Processors',
          'KQL Telemetry Queries & Windowing Functions'
        ]
      },
      domain3: {
        id: 'domain3',
        code: 'Domain 3',
        name: 'Monitor and optimize an analytics solution',
        percentage: '25–30%',
        minWeight: 0.25,
        maxWeight: 0.30,
        description: 'Monitor hub, Activator alerts, notebook session timeouts, Delta table maintenance, Spark pools, autoscaling, and concurrency.',
        keyTopics: [
          'Monitor Hub & Activity Status/Start Time Filtering',
          'Fabric Activator Changing Data Alerts',
          'Delta Lake (V-Order, OPTIMIZE, autoCompact, optimizeWrite)',
          'Custom Spark Pools & Dynamic Executor Allocation',
          'Pipeline Error Handling & Fail Activities'
        ]
      }
    }
  },
  dp600: {
    id: 'dp600',
    code: 'DP-600',
    title: 'Implementing Analytics Solutions Using Microsoft Fabric',
    shortTitle: 'Fabric Analytics Engineer',
    badge: 'Fabric Analytics Engineer Associate',
    targetRole: 'Analytics Engineers & BI Professionals',
    description: 'Transform, model, and serve analytics-ready data assets in Microsoft Fabric with Power BI, semantic models, Direct Lake, and DAX calculations.',
    domains: {
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
    }
  }
};

export function getDomainsForExam(examId: ExamId = 'dp700'): Record<DomainId, DomainInfo> {
  return EXAMS[examId]?.domains || EXAMS.dp700.domains;
}

// Backward compatibility default
export const DOMAINS: Record<DomainId, DomainInfo> = EXAMS.dp700.domains;

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
  examId?: ExamId;
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
  examId?: ExamId;
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
  examId?: ExamId | 'all';
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
