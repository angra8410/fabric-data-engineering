import React, { useMemo } from 'react';
import { UserStats, Question, DOMAINS, DomainId } from '../types';
import { 
  TrendingUp, 
  Flame, 
  Target, 
  CheckCircle2, 
  Award, 
  Clock, 
  AlertTriangle, 
  Layers, 
  Database, 
  ShieldCheck, 
  ArrowRight,
  Sparkles,
  BarChart3
} from 'lucide-react';

interface PerformanceAnalyticsProps {
  stats: UserStats;
  questions: Question[];
  onStartPractice: (domain?: DomainId) => void;
  onStartExam: () => void;
}

export const PerformanceAnalytics: React.FC<PerformanceAnalyticsProps> = ({
  stats,
  questions,
  onStartPractice,
  onStartExam
}) => {
  const overallAccuracy = stats.totalAnswered > 0
    ? Math.round((stats.correctAnswers / stats.totalAnswered) * 100)
    : 0;

  const mockExamsCount = stats.examAttempts.length;
  const passedExamsCount = stats.examAttempts.filter(a => a.passed).length;
  const passRate = mockExamsCount > 0
    ? Math.round((passedExamsCount / mockExamsCount) * 100)
    : 0;

  // Average pacing
  const averagePacingSeconds = useMemo(() => {
    if (stats.examAttempts.length > 0) {
      const totalSecs = stats.examAttempts.reduce((acc, a) => acc + (a.timeSpentSeconds || 0), 0);
      const totalQs = stats.examAttempts.reduce((acc, a) => acc + (a.totalQuestions || 40), 0);
      if (totalQs > 0) return Math.max(25, Math.round(totalSecs / totalQs));
    }
    return 44;
  }, [stats.examAttempts]);

  // Domain accuracy breakdown to identify weakest domain
  const domainStats = useMemo(() => {
    const counts: Record<DomainId, { total: number; correct: number }> = {
      domain1: { total: 0, correct: 0 },
      domain2: { total: 0, correct: 0 },
      domain3: { total: 0, correct: 0 }
    };

    questions.forEach(q => {
      const attempt = stats.answeredQuestionIds[q.id];
      if (attempt) {
        counts[q.domain].total += 1;
        if (attempt.isCorrect) counts[q.domain].correct += 1;
      }
    });

    return (Object.keys(counts) as DomainId[]).map(dId => {
      const d = counts[dId];
      const acc = d.total > 0 ? Math.round((d.correct / d.total) * 100) : 0;
      return {
        id: dId,
        info: DOMAINS[dId],
        total: d.total,
        correct: d.correct,
        accuracy: acc
      };
    });
  }, [questions, stats.answeredQuestionIds]);

  // Weakest domain (primary focus area)
  const primaryFocusDomain = useMemo(() => {
    const attemptedDomains = domainStats.filter(d => d.total > 0);
    if (attemptedDomains.length === 0) return domainStats[1]; // default domain 2
    return [...attemptedDomains].sort((a, b) => a.accuracy - b.accuracy)[0];
  }, [domainStats]);

  // Score Progression Points (History Curve)
  const scorePoints = useMemo(() => {
    if (stats.examAttempts.length === 0) {
      // Sample baseline points showing passing line
      return [
        { label: '#1', score: 720, percentage: 72 },
        { label: '#2', score: 800, percentage: 80 }
      ];
    }
    return stats.examAttempts.slice().reverse().map((att, idx) => ({
      label: `#${idx + 1}`,
      score: att.score,
      percentage: Math.min(100, Math.round((att.score / 1000) * 100))
    }));
  }, [stats.examAttempts]);

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-20 animate-fade-in text-white">
      
      {/* Hero Header matching Reference Screenshots 1 & 2 */}
      <div className="space-y-1.5">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-amber-400" />
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Performance Telemetry & Analytics
          </h1>
        </div>
        <p className="text-xs sm:text-sm text-slate-300">
          Historical assessment tracking, pacing metrics, domain strengths, and adaptive topic analysis.
        </p>
      </div>

      {/* Top 4 Stat Cards matching Reference Screenshot 1 & 2 */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        
        {/* 1. Daily Streak */}
        <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-5 shadow-xl flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center shrink-0 text-amber-400">
            <Flame className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xl sm:text-2xl font-black text-white">
              {stats.streakDays} <span className="text-xs font-semibold text-slate-400">Days</span>
            </div>
            <div className="text-[11px] font-medium text-slate-400">Daily Streak</div>
          </div>
        </div>

        {/* 2. Questions Answered */}
        <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-5 shadow-xl flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center shrink-0 text-sky-400">
            <Target className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xl sm:text-2xl font-black text-white">
              {stats.totalAnswered}
            </div>
            <div className="text-[11px] font-medium text-slate-400">Questions Answered</div>
          </div>
        </div>

        {/* 3. Overall Accuracy */}
        <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-5 shadow-xl flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0 text-emerald-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xl sm:text-2xl font-black text-white">
              {overallAccuracy}%
            </div>
            <div className="text-[11px] font-medium text-slate-400">Overall Accuracy</div>
          </div>
        </div>

        {/* 4. Mock Exams Done */}
        <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-5 shadow-xl flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center shrink-0 text-purple-400">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xl sm:text-2xl font-black text-white">
              {mockExamsCount}
            </div>
            <div className="text-[11px] font-medium text-slate-400">Mock Exams Done</div>
          </div>
        </div>

      </div>

      {/* Middle 3 Secondary Metric Cards matching Reference Screenshots 1 & 2 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        {/* 1. Average Pacing */}
        <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-6 shadow-xl space-y-3">
          <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-amber-400">
            <Clock className="w-4 h-4 text-amber-400" />
            <span>AVERAGE PACING</span>
          </div>
          <div className="text-3xl font-black text-white tracking-tight">
            {averagePacingSeconds}s <span className="text-sm font-normal text-slate-400">/ Question</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Exam target is ~135 seconds per question. You are well within the safe speed threshold.
          </p>
        </div>

        {/* 2. Mock Exam Pass Rate */}
        <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-6 shadow-xl space-y-3">
          <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-emerald-400">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>MOCK EXAM PASS RATE</span>
          </div>
          <div className="text-3xl font-black text-emerald-400 tracking-tight">
            {mockExamsCount > 0 ? `${passRate}%` : '100%'}
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Passing threshold: 70% (700 scaled mark). Maintain regular simulation tests to stay sharp.
          </p>
        </div>

        {/* 3. Primary Focus Area */}
        <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-6 shadow-xl space-y-3">
          <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-rose-400">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <span>PRIMARY FOCUS AREA</span>
          </div>
          <div className="text-xl sm:text-2xl font-black text-white tracking-tight truncate">
            {primaryFocusDomain.info.name}
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Current domain accuracy: <strong className="text-white">{primaryFocusDomain.accuracy}%</strong>. Drill these questions to raise your overall average.
          </p>
        </div>

      </div>

      {/* Score History & Progression Curve Chart matching Reference Screenshots 1 & 2 */}
      <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">Score History & Progression Curve</h2>
            <p className="text-xs text-slate-400">Trajectory of your recent practice and mock exam attempts over time.</p>
          </div>
          <div className="text-xs font-mono text-emerald-400 font-semibold flex items-center gap-2">
            <span className="w-4 h-0.5 border-t-2 border-dashed border-emerald-400 inline-block"></span>
            <span>Green Line = Pass Threshold (70%)</span>
          </div>
        </div>

        {/* Interactive SVG Line Graph */}
        <div className="w-full overflow-x-auto">
          <div className="min-w-[500px] h-64 relative pt-4 pb-8 px-8">
            <svg className="w-full h-full overflow-visible" viewBox="0 0 500 160">
              
              {/* Horizontal Grid Lines */}
              {[0, 25, 50, 75, 100].map((val) => {
                const y = 140 - (val / 100) * 120;
                return (
                  <g key={val}>
                    <line x1="0" y1={y} x2="500" y2={y} stroke="#1E293B" strokeWidth="1" />
                    <text x="-10" y={y + 4} fill="#64748B" fontSize="9" textAnchor="end">{val}</text>
                  </g>
                );
              })}

              {/* 70% Pass Threshold Line (Green Dashed) */}
              <line
                x1="0"
                y1={140 - (70 / 100) * 120}
                x2="500"
                y2={140 - (70 / 100) * 120}
                stroke="#10B981"
                strokeWidth="1.5"
                strokeDasharray="4 4"
              />
              <text x="505" y={140 - (70 / 100) * 120 + 3} fill="#10B981" fontSize="9">Pass (70%)</text>

              {/* Score Trend Line */}
              {(() => {
                const count = scorePoints.length;
                const pointsCoords = scorePoints.map((pt, idx) => {
                  const x = count === 1 ? 250 : (idx / (count - 1)) * 480 + 10;
                  const y = 140 - (pt.percentage / 100) * 120;
                  return { x, y, pt };
                });

                const pathData = pointsCoords.reduce((acc, curr, i) => {
                  return i === 0 ? `M ${curr.x} ${curr.y}` : `${acc} L ${curr.x} ${curr.y}`;
                }, '');

                return (
                  <g>
                    <path
                      d={pathData}
                      fill="none"
                      stroke="#FACC15"
                      strokeWidth="3"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />

                    {pointsCoords.map((coord, i) => (
                      <g key={i}>
                        <circle
                          cx={coord.x}
                          cy={coord.y}
                          r="5"
                          fill="#FACC15"
                          stroke="#0B101D"
                          strokeWidth="2"
                        />
                        <text
                          x={coord.x}
                          y={coord.y - 10}
                          fill="#FDE047"
                          fontSize="10"
                          fontWeight="bold"
                          textAnchor="middle"
                        >
                          {coord.pt.score} pts
                        </text>
                        <text
                          x={coord.x}
                          y="155"
                          fill="#94A3B8"
                          fontSize="10"
                          textAnchor="middle"
                        >
                          {coord.pt.label}
                        </text>
                      </g>
                    ))}
                  </g>
                );
              })()}

            </svg>
          </div>
        </div>

      </div>

      {/* Domain Proficiency Breakdown Cards */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider text-slate-400">
          Domain Proficiency Distribution
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {domainStats.map((d) => (
            <div key={d.id} className="bg-[#10172A] border border-slate-800 rounded-2xl p-5 space-y-3 shadow-lg">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-teal-300 bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/20">
                  {d.info.code}
                </span>
                <span className="text-xs font-bold text-white">{d.accuracy}%</span>
              </div>
              <h4 className="text-sm font-bold text-white leading-snug">{d.info.name}</h4>
              
              {/* Progress Bar */}
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-500 ${
                    d.accuracy >= 70 ? 'bg-emerald-400' : d.accuracy >= 50 ? 'bg-amber-400' : 'bg-rose-400'
                  }`}
                  style={{ width: `${d.accuracy}%` }}
                />
              </div>

              <div className="flex justify-between items-center text-[11px] text-slate-400 pt-1">
                <span>{d.correct} of {d.total} correct</span>
                <button
                  onClick={() => onStartPractice(d.id)}
                  className="text-teal-400 hover:text-teal-300 font-semibold flex items-center gap-1"
                >
                  <span>Drill</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
export default PerformanceAnalytics;
