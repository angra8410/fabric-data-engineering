import React from 'react';
import { UserStats, Question, DomainId } from '../types';
import { 
  Calendar, 
  CheckCircle2, 
  Flame, 
  Play, 
  RotateCcw, 
  BookOpen, 
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Layers,
  Database,
  Code2,
  Cpu,
  BarChart3,
  Award
} from 'lucide-react';

interface SevenDayPlanProps {
  stats: UserStats;
  questions: Question[];
  onStartDay: (dayNumber: number, domainFilter?: DomainId, topicKeyword?: string) => void;
  onStartExam: () => void;
  onViewStudyGuide: (domainFilter?: DomainId) => void;
}

interface DayPlan {
  day: number;
  tag: string;
  domain: DomainId;
  topicKeyword?: string;
  title: string;
  description: string;
  topics: string[];
  icon: React.ReactNode;
  isExamDay?: boolean;
}

export const SevenDayPlan: React.FC<SevenDayPlanProps> = ({
  stats,
  questions,
  onStartDay,
  onStartExam,
  onViewStudyGuide
}) => {
  const days: DayPlan[] = [
    {
      day: 1,
      tag: 'Workspaces & CU Admin',
      domain: 'domain1',
      title: 'Domain 1: Plan, implement, and manage an analytics solution',
      description: 'Master Fabric capacities, smoothing, throttling, workspace roles, Git integration, and deployment pipelines.',
      topics: ['Capacity & Workspace Admin', 'Deployment Pipelines & Git', 'OneLake Security & Governance', 'Monitoring & Tenant Settings'],
      icon: <ShieldCheck className="w-5 h-5 text-teal-400" />
    },
    {
      day: 2,
      tag: 'OneLake Shortcuts',
      domain: 'domain2',
      topicKeyword: 'shortcut',
      title: 'Domain 2: OneLake Architecture & Shortcuts',
      description: 'Internal vs external shortcuts, ADLS Gen2, Amazon S3, OneLake security and folder paths.',
      topics: ['Internal Shortcuts', 'ADLS Gen2 Shortcuts', 'Amazon S3 Shortcuts', 'Tables vs Files Structure'],
      icon: <Layers className="w-5 h-5 text-sky-400" />
    },
    {
      day: 3,
      tag: 'Delta Lake & V-Order',
      domain: 'domain2',
      topicKeyword: 'delta',
      title: 'Domain 2: Delta Lake Optimization & Engine',
      description: 'Delta Parquet storage, V-Order encoding for VertiPaq, OPTIMIZE ZORDER BY, and VACUUM retention periods.',
      topics: ['V-Order Encoding', 'OPTIMIZE ZORDER BY', 'VACUUM Retention', 'Delta Log & Parquet'],
      icon: <Database className="w-5 h-5 text-emerald-400" />
    },
    {
      day: 4,
      tag: 'PySpark & Dataflows',
      domain: 'domain2',
      title: 'Domain 2: Lakehouse vs Warehouse & Data Transformation',
      description: 'When to choose Lakehouse vs Warehouse, cross-database T-SQL, PySpark DataFrames, and Dataflows Gen2.',
      topics: ['Lakehouse vs Warehouse', 'PySpark Transformations', 'T-SQL Joins & CTAS', 'Dataflows Gen2'],
      icon: <Code2 className="w-5 h-5 text-amber-400" />
    },
    {
      day: 5,
      tag: 'Direct Lake Modeling',
      domain: 'domain3',
      topicKeyword: 'direct lake',
      title: 'Domain 3: Direct Lake Semantic Models & Fallback',
      description: 'Direct Lake performance, Delta Parquet requirements, fallback conditions to DirectQuery, and memory framing.',
      topics: ['Direct Lake Requirements', 'VertiPaq Memory Limits', 'Fallback to DirectQuery', 'Framing & Auto-Sync'],
      icon: <Cpu className="w-5 h-5 text-purple-400" />
    },
    {
      day: 6,
      tag: 'DAX & Calc Groups',
      domain: 'domain3',
      title: 'Domain 3: DAX Calculations & Semantic Modeling',
      description: 'Star schema design, Calculation Groups with SELECTEDMEASURE(), Field Parameters, and DAX Studio tuning.',
      topics: ['Star Schema Fact & Dim', 'Calculation Groups', 'Field Parameters', 'DAX Studio Profiling'],
      icon: <BarChart3 className="w-5 h-5 text-rose-400" />
    },
    {
      day: 7,
      tag: 'Full 100m Mock Exam',
      domain: 'domain1',
      title: 'Comprehensive DP-600 Mock Exam (100 mins)',
      description: 'Full 40-question timed exam under Pearson VUE conditions with case studies, multi-select, and drag-and-drop sequencing.',
      topics: ['40 Timed Questions', '100 Minutes', 'Case Study Analysis', 'Official Pass Mark: 700 / 1000'],
      icon: <Award className="w-5 h-5 text-amber-400" />,
      isExamDay: true
    }
  ];

  // Calculate day completion and accuracy metrics
  const getDayStatus = (day: DayPlan) => {
    if (day.isExamDay) {
      const attempts = stats.examAttempts || [];
      if (attempts.length === 0) return { completed: false, score: null, attemptedCount: 0, totalCount: 40 };
      const latest = attempts[0];
      return { completed: true, score: Math.round((latest.score / 1000) * 100), attemptedCount: latest.totalQuestions, totalCount: 40 };
    }

    const dayQuestions = questions.filter(q => {
      if (day.topicKeyword) {
        return q.domain === day.domain && (
          q.topic.toLowerCase().includes(day.topicKeyword) ||
          q.text.toLowerCase().includes(day.topicKeyword)
        );
      }
      return q.domain === day.domain;
    });

    const totalCount = dayQuestions.length;
    let answered = 0;
    let correct = 0;

    dayQuestions.forEach(q => {
      const att = stats.answeredQuestionIds[q.id];
      if (att) {
        answered++;
        if (att.isCorrect) correct++;
      }
    });

    const score = answered > 0 ? Math.round((correct / answered) * 100) : null;
    const completed = answered >= Math.min(10, totalCount);

    return { completed, score, attemptedCount: answered, totalCount };
  };

  const finishedDaysCount = days.filter(d => getDayStatus(d).completed).length;

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16 animate-fade-in text-white">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-br from-slate-900 via-[#0B1528] to-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-teal-500/5 rounded-full blur-3xl pointer-events-none"></div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative z-10">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-semibold">
              <Calendar className="w-3.5 h-3.5" />
              <span>STRUCTURED 7-DAY ROADMAP</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              7-Day <span className="bg-gradient-to-r from-teal-400 via-sky-400 to-blue-400 bg-clip-text text-transparent">DP-600 Study Roadmap</span>
            </h1>
            <p className="text-sm text-slate-300 leading-relaxed">
              Eliminate study guesswork. Follow our day-by-day training sequence to systematically conquer each section of the syllabus, from Fabric capacities to full-length exam execution.
            </p>
          </div>

          <div className="flex sm:flex-col items-center sm:items-end gap-3 shrink-0">
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700/60 text-xs font-semibold text-emerald-300 shadow-inner">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{finishedDaysCount} of 7 Days Finished</span>
            </div>
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-orange-500/10 border border-orange-500/20 text-xs font-semibold text-orange-400">
              <Flame className="w-4 h-4 text-orange-400 animate-pulse" />
              <span>Streak: {stats.streakDays} Days</span>
            </div>
          </div>
        </div>
      </div>

      {/* Day Cards List */}
      <div className="space-y-4">
        {days.map((d) => {
          const status = getDayStatus(d);

          return (
            <div 
              key={d.day}
              className={`p-6 rounded-2xl border transition-all duration-200 bg-[#0F172A]/80 backdrop-blur-sm shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6 hover:border-slate-600 ${
                status.completed
                  ? 'border-emerald-500/30 bg-gradient-to-r from-slate-900 to-[#0A1D24]'
                  : 'border-slate-800 hover:bg-slate-900/90'
              }`}
            >
              {/* Left Column: Day Badge & Info */}
              <div className="flex items-start gap-4 flex-1">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 mt-0.5 border ${
                  status.completed 
                    ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300' 
                    : 'bg-slate-800 border-slate-700 text-slate-300'
                }`}>
                  {status.completed ? (
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                  ) : (
                    d.icon
                  )}
                </div>

                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-extrabold text-xs tracking-wider text-amber-400 uppercase">
                      DAY {d.day}
                    </span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                      {d.tag}
                    </span>
                    {status.score !== null && (
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-md border ${
                        status.score >= 70
                          ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                          : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                      }`}>
                        {status.score}% Score ({status.attemptedCount}/{status.totalCount} Qs)
                      </span>
                    )}
                  </div>

                  <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                    {d.title}
                  </h3>

                  <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                    {d.description}
                  </p>

                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    {d.topics.map((t, idx) => (
                      <span 
                        key={idx}
                        className="text-[11px] font-medium px-2 py-0.5 rounded bg-slate-950/60 border border-slate-800 text-slate-400"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right Column: Action Button */}
              <div className="flex items-center gap-2.5 shrink-0 justify-end pt-2 md:pt-0 border-t md:border-t-0 border-slate-800">
                {d.isExamDay ? (
                  <button
                    onClick={onStartExam}
                    className="w-full md:w-auto px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-extrabold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-lg shadow-amber-500/20 active:scale-95 transition-all cursor-pointer"
                  >
                    <Play className="w-4 h-4 fill-slate-950" />
                    <span>Start Mock Exam (40 Qs)</span>
                  </button>
                ) : status.completed ? (
                  <button
                    onClick={() => onStartDay(d.day, d.domain, d.topicKeyword)}
                    className="w-full md:w-auto px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs flex items-center justify-center gap-2 border border-slate-700 transition-all cursor-pointer"
                  >
                    <RotateCcw className="w-3.5 h-3.5 text-teal-400" />
                    <span>Retake Day {d.day}</span>
                  </button>
                ) : (
                  <button
                    onClick={() => onStartDay(d.day, d.domain, d.topicKeyword)}
                    className="w-full md:w-auto px-5 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-extrabold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-lg shadow-teal-500/20 active:scale-95 transition-all cursor-pointer"
                  >
                    <Play className="w-4 h-4 fill-slate-950" />
                    <span>Start Day {d.day} ({status.totalCount} Qs)</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
};
