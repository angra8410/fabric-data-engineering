import React, { useMemo } from 'react';
import { UserStats, DOMAINS, DomainId, Question, ExamAttempt } from '../types';
import { 
  Award, 
  Flame, 
  Target, 
  CheckCircle2, 
  PlayCircle, 
  UploadCloud, 
  Clock, 
  ArrowRight, 
  Layers,
  Database,
  BarChart3,
  TrendingUp,
  XCircle,
  Sparkles,
  BookOpen,
  Play,
  Zap,
  ShieldCheck
} from 'lucide-react';
import { ActiveTab } from './Navbar';

interface DashboardProps {
  stats: UserStats;
  questions: Question[];
  totalQuestions: number;
  setActiveTab: (tab: ActiveTab) => void;
  onFilterDomain: (domain: DomainId) => void;
  onSelectAttempt?: (attempt: ExamAttempt) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  stats,
  questions,
  totalQuestions,
  setActiveTab,
  onFilterDomain,
  onSelectAttempt
}) => {
  const accuracy = stats.totalAnswered > 0 
    ? Math.round((stats.correctAnswers / stats.totalAnswered) * 100) 
    : 0;

  // Domain question statistics
  const domainCounts = useMemo(() => {
    const counts: Record<DomainId, { total: number; answered: number; correct: number }> = {
      domain1: { total: 0, answered: 0, correct: 0 },
      domain2: { total: 0, answered: 0, correct: 0 },
      domain3: { total: 0, answered: 0, correct: 0 }
    };
    questions.forEach(q => {
      if (counts[q.domain]) {
        counts[q.domain].total++;
        const ans = stats.answeredQuestionIds[q.id];
        if (ans) {
          counts[q.domain].answered++;
          if (ans.isCorrect) counts[q.domain].correct++;
        }
      }
    });
    return counts;
  }, [questions, stats]);

  // Estimated readiness score (200 - 1000 scale)
  const estimatedScore = stats.totalAnswered === 0 
    ? 300 
    : Math.min(1000, Math.round(200 + 800 * (accuracy / 100)));

  const isReady = estimatedScore >= 700;

  const latestExam = stats.examAttempts.length > 0 ? stats.examAttempts[0] : null;

  const recommendedDomainId: DomainId = useMemo(() => {
    let worstDomain: DomainId = 'domain2';
    let minAcc = 101;
    (['domain1', 'domain2', 'domain3'] as DomainId[]).forEach(d => {
      const data = domainCounts[d];
      const acc = data.answered > 0 ? (data.correct / data.answered) * 100 : 0;
      if (acc < minAcc) {
        minAcc = acc;
        worstDomain = d;
      }
    });
    return worstDomain;
  }, [domainCounts]);

  const recommendedInfo = DOMAINS[recommendedDomainId];
  const recommendedAcc = domainCounts[recommendedDomainId].answered > 0 
    ? Math.round((domainCounts[recommendedDomainId].correct / domainCounts[recommendedDomainId].answered) * 100)
    : 0;

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      
      {/* Hero Banner (Matches Reference Screenshot) */}
      <div className="relative overflow-hidden rounded-3xl bg-[#0F172A]/70 border border-slate-800 p-6 sm:p-8 shadow-2xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          
          {/* Left Column (lg:col-span-7) */}
          <div className="lg:col-span-7 space-y-4">
            
            {/* Pill Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30 text-xs font-bold tracking-wide uppercase">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>Fabric Analytics Engineer Associate Certification</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
              Master the <span className="text-amber-400">DP-600 Exam</span> with Realistic Simulation
            </h1>

            {/* Subtitle */}
            <p className="text-sm sm:text-base text-slate-300 max-w-2xl leading-relaxed">
              Train across all 3 Microsoft assessment domains with {totalQuestions} original scenario questions, live Direct Lake mode diagnostics, Delta Lake V-Order optimizations, and an adaptive 7-day study plan.
            </p>

            {/* 3 Feature Verification Badges */}
            <div className="flex flex-wrap items-center gap-2.5 pt-1">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/90 border border-slate-800 text-xs font-semibold text-slate-300">
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
                <span>{totalQuestions} Verified Questions</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/90 border border-slate-800 text-xs font-semibold text-slate-300">
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
                <span>Deep Fabric & DAX Explanations</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/90 border border-slate-800 text-xs font-semibold text-slate-300">
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
                <span>Local Storage Saved</span>
              </div>
            </div>

            {/* Recommended Next Step Box */}
            <div className="mt-4 p-4 rounded-2xl bg-slate-900/90 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg">
              <div className="flex items-center gap-3.5">
                <div className="w-11 h-11 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
                  <BookOpen className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-[10px] font-bold text-amber-400 uppercase tracking-wider mb-0.5">
                    RECOMMENDED NEXT STEP:
                  </div>
                  <div className="text-xs text-slate-200 leading-snug">
                    Focus on {recommendedInfo.keyTopics[0]} ({recommendedAcc}% accuracy) in {recommendedInfo.name}. Practice targeted questions.
                  </div>
                </div>
              </div>

              <button
                onClick={() => onFilterDomain(recommendedDomainId)}
                className="px-4 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs flex items-center justify-center gap-1.5 shrink-0 transition-colors shadow-sm"
              >
                <Play className="w-3.5 h-3.5 fill-slate-950" />
                <span>Continue Training</span>
              </button>
            </div>

          </div>

          {/* Right Column: Certification Goal Card (lg:col-span-5) */}
          <div className="lg:col-span-5 bg-[#10172A] border border-slate-800 rounded-2xl p-6 space-y-5 shadow-2xl flex flex-col justify-between">
            
            {/* Card Header */}
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold text-white">Certification Goal</span>
                    <span className="bg-amber-400/20 text-amber-300 text-[10px] font-extrabold px-1.5 py-0.5 rounded border border-amber-500/30">
                      DP-600
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Passing Threshold: 700 / 1000 pts
                  </div>
                </div>
              </div>

              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                <span>{accuracy >= 70 ? 'Ready' : 'In Progress'}</span>
              </span>
            </div>

            {/* Current Average Score & Target Bar */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1.5 font-medium">
                <span className="text-slate-400">Current Average Score</span>
                <span className="text-white font-bold text-sm">{accuracy}%</span>
              </div>

              <div className="relative w-full bg-slate-800 rounded-full h-2.5 my-2">
                <div 
                  className={`h-full rounded-full transition-all duration-500 ${
                    accuracy >= 70 ? 'bg-gradient-to-r from-amber-400 to-emerald-400' : 'bg-amber-400'
                  }`}
                  style={{ width: `${Math.min(100, Math.max(2, accuracy))}%` }}
                />
                {/* 70% threshold tick indicator */}
                <div className="absolute top-0 bottom-0 left-[70%] w-0.5 bg-slate-400 -translate-x-1/2" />
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium">
                <span>0%</span>
                <span className="flex items-center gap-1 text-amber-400 font-semibold">
                  <Target className="w-3 h-3 text-amber-400" />
                  Pass Mark: 70%
                </span>
                <span>100%</span>
              </div>
            </div>

            {/* 3 Mini-Stats Grid */}
            <div className="grid grid-cols-3 gap-2.5 text-center">
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3">
                <div className="text-xl font-black text-white">{totalQuestions}</div>
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">QUESTIONS</div>
              </div>
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3">
                <div className="text-xl font-black text-white">3</div>
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">DOMAINS</div>
              </div>
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3">
                <div className="text-xl font-black text-white">100m</div>
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">TIMED</div>
              </div>
            </div>

            {/* CTA Action Buttons */}
            <div className="flex items-center gap-2.5 pt-1">
              <button
                onClick={() => setActiveTab('mock-exam')}
                className="flex-1 py-2.5 px-3 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors shadow-md shadow-amber-400/20 active:scale-[0.99]"
              >
                <Clock className="w-4 h-4" />
                <span>Timed Mock Exam (100m)</span>
              </button>
              <button
                onClick={() => setActiveTab('practice')}
                className="flex-1 py-2.5 px-3 rounded-xl bg-slate-800/90 hover:bg-slate-700/90 border border-slate-700 text-slate-200 hover:text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-colors active:scale-[0.99]"
              >
                <Zap className="w-4 h-4 text-amber-400" />
                <span>Explore {totalQuestions} Qs</span>
              </button>
            </div>

          </div>

        </div>
      </div>

      {/* 4 Metrics Statistics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        
        {/* Streak */}
        <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center shrink-0">
            <Flame className="w-6 h-6 text-orange-400 animate-pulse" />
          </div>
          <div>
            <div className="text-xl sm:text-2xl font-black text-white">{stats.streakDays} Days</div>
            <div className="text-xs text-slate-400 font-medium">Study Streak</div>
          </div>
        </div>

        {/* Total Questions Practiced */}
        <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center shrink-0">
            <CheckCircle2 className="w-6 h-6 text-teal-400" />
          </div>
          <div>
            <div className="text-xl sm:text-2xl font-black text-white">{stats.totalAnswered} / {totalQuestions}</div>
            <div className="text-xs text-slate-400 font-medium">Questions Attempted</div>
          </div>
        </div>

        {/* Accuracy */}
        <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center shrink-0">
            <Target className="w-6 h-6 text-sky-400" />
          </div>
          <div>
            <div className="text-xl sm:text-2xl font-black text-white">{accuracy}%</div>
            <div className="text-xs text-slate-400 font-medium">Overall Accuracy</div>
          </div>
        </div>

        {/* Mock Exams Done */}
        <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center shrink-0">
            <Award className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <div className="text-xl sm:text-2xl font-black text-white">{stats.examAttempts.length}</div>
            <div className="text-xs text-slate-400 font-medium">Mock Exams Taken</div>
          </div>
        </div>

      </div>

      {/* Official Skills Measured (DP-600 Breakdown - Matches Reference Screenshot) */}
      <div className="space-y-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
            DP-600 Skills Measured
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
            Exam domain breakdown based on official Microsoft specifications.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Domain 1: Plan, implement, and manage */}
          {(() => {
            const d = 'domain1' as DomainId;
            const info = DOMAINS[d];
            const data = domainCounts[d];
            const acc = data.answered > 0 ? Math.round((data.correct / data.answered) * 100) : 0;
            return (
              <div 
                key={d}
                className="bg-[#10172A] border border-slate-800 hover:border-slate-700/80 rounded-2xl p-5 sm:p-6 flex flex-col justify-between transition-all group shadow-xl"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center shrink-0">
                      <Database className="w-6 h-6" />
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700/50">
                      {info.percentage}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white mb-2 leading-snug group-hover:text-blue-300 transition-colors">
                    {info.name}
                  </h3>
                  <p className="text-xs text-slate-400 leading-relaxed mb-6 line-clamp-2">
                    {info.description}
                  </p>
                </div>

                <div>
                  <div className="flex items-center justify-between text-xs mb-2">
                    <span className="text-slate-400 font-medium">Mastery Accuracy</span>
                    <span className="text-emerald-400 font-bold">{acc}%</span>
                  </div>

                  <div className="w-full bg-slate-800/80 rounded-full h-2 mb-5 overflow-hidden">
                    <div 
                      className="h-full rounded-full bg-emerald-400 transition-all duration-500"
                      style={{ width: `${acc}%` }}
                    />
                  </div>

                  <button
                    onClick={() => onFilterDomain(d)}
                    className="w-full py-2.5 px-4 rounded-xl bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-200 hover:text-white text-xs font-bold flex items-center justify-center gap-1.5 transition-all shadow-sm active:scale-[0.99]"
                  >
                    <span>Practice Domain ({data.total} Qs)</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-white" />
                  </button>
                </div>
              </div>
            );
          })()}

          {/* Domain 2: Prepare and connect to data */}
          {(() => {
            const d = 'domain2' as DomainId;
            const info = DOMAINS[d];
            const data = domainCounts[d];
            const acc = data.answered > 0 ? Math.round((data.correct / data.answered) * 100) : 0;
            return (
              <div 
                key={d}
                className="bg-[#10172A] border border-slate-800 hover:border-slate-700/80 rounded-2xl p-5 sm:p-6 flex flex-col justify-between transition-all group shadow-xl"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center shrink-0">
                      <Layers className="w-6 h-6" />
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700/50">
                      {info.percentage}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white mb-2 leading-snug group-hover:text-purple-300 transition-colors">
                    {info.name}
                  </h3>
                  <p className="text-xs text-slate-400 leading-relaxed mb-6 line-clamp-2">
                    {info.description}
                  </p>
                </div>

                <div>
                  <div className="flex items-center justify-between text-xs mb-2">
                    <span className="text-slate-400 font-medium">Mastery Accuracy</span>
                    <span className="text-emerald-400 font-bold">{acc}%</span>
                  </div>

                  <div className="w-full bg-slate-800/80 rounded-full h-2 mb-5 overflow-hidden">
                    <div 
                      className="h-full rounded-full bg-emerald-400 transition-all duration-500"
                      style={{ width: `${acc}%` }}
                    />
                  </div>

                  <button
                    onClick={() => onFilterDomain(d)}
                    className="w-full py-2.5 px-4 rounded-xl bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-200 hover:text-white text-xs font-bold flex items-center justify-center gap-1.5 transition-all shadow-sm active:scale-[0.99]"
                  >
                    <span>Practice Domain ({data.total} Qs)</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-white" />
                  </button>
                </div>
              </div>
            );
          })()}

          {/* Domain 3: Model and explore data */}
          {(() => {
            const d = 'domain3' as DomainId;
            const info = DOMAINS[d];
            const data = domainCounts[d];
            const acc = data.answered > 0 ? Math.round((data.correct / data.answered) * 100) : 0;
            return (
              <div 
                key={d}
                className="bg-[#10172A] border border-slate-800 hover:border-slate-700/80 rounded-2xl p-5 sm:p-6 flex flex-col justify-between transition-all group shadow-xl"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                      <BarChart3 className="w-6 h-6" />
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700/50">
                      {info.percentage}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white mb-2 leading-snug group-hover:text-emerald-300 transition-colors">
                    {info.name}
                  </h3>
                  <p className="text-xs text-slate-400 leading-relaxed mb-6 line-clamp-2">
                    {info.description}
                  </p>
                </div>

                <div>
                  <div className="flex items-center justify-between text-xs mb-2">
                    <span className="text-slate-400 font-medium">Mastery Accuracy</span>
                    <span className="text-emerald-400 font-bold">{acc}%</span>
                  </div>

                  <div className="w-full bg-slate-800/80 rounded-full h-2 mb-5 overflow-hidden">
                    <div 
                      className="h-full rounded-full bg-emerald-400 transition-all duration-500"
                      style={{ width: `${acc}%` }}
                    />
                  </div>

                  <button
                    onClick={() => onFilterDomain(d)}
                    className="w-full py-2.5 px-4 rounded-xl bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-200 hover:text-white text-xs font-bold flex items-center justify-center gap-1.5 transition-all shadow-sm active:scale-[0.99]"
                  >
                    <span>Practice Domain ({data.total} Qs)</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-white" />
                  </button>
                </div>
              </div>
            );
          })()}
        </div>
      </div>

      {/* Domain Mastery Radar & Recent Exam Attempts (Matches Reference Screenshot) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        
        {/* Left: Domain Mastery Radar (Spider Chart) */}
        <div className="lg:col-span-5 bg-[#10172A] border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-xl">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-base font-bold text-white">Domain Mastery Radar</h3>
            <span className="text-xs font-semibold text-teal-400 bg-teal-500/10 border border-teal-500/20 px-2.5 py-0.5 rounded-full">
              Target: 80%
            </span>
          </div>

          {/* SVG Radar Chart */}
          <div className="flex items-center justify-center py-2">
            {(() => {
              const cx = 150;
              const cy = 120;
              const R = 75;

              // 3 axes:
              // Axis 0 (top): Plan & Manage
              // Axis 1 (bottom-right): Prepare & Connect
              // Axis 2 (bottom-left): Model & Explore
              const angles = [-Math.PI / 2, -Math.PI / 2 + (2 * Math.PI) / 3, -Math.PI / 2 + (4 * Math.PI) / 3];

              const getCoord = (angle: number, radius: number) => ({
                x: cx + radius * Math.cos(angle),
                y: cy + radius * Math.sin(angle)
              });

              const rings = [0.25, 0.50, 0.75, 1.0];

              // Target ring at 80%
              const targetPoints = angles.map(a => {
                const pt = getCoord(a, R * 0.8);
                return `${pt.x},${pt.y}`;
              }).join(' ');

              // User polygon
              const d1Acc = domainCounts.domain1.answered > 0 ? Math.round((domainCounts.domain1.correct / domainCounts.domain1.answered) * 100) : 0;
              const d2Acc = domainCounts.domain2.answered > 0 ? Math.round((domainCounts.domain2.correct / domainCounts.domain2.answered) * 100) : 0;
              const d3Acc = domainCounts.domain3.answered > 0 ? Math.round((domainCounts.domain3.correct / domainCounts.domain3.answered) * 100) : 0;
              const userAccs = [d1Acc, d2Acc, d3Acc];

              const userPoints = angles.map((a, i) => {
                const scoreFrac = Math.max(0.12, Math.min(1.0, userAccs[i] / 100));
                const pt = getCoord(a, R * scoreFrac);
                return `${pt.x},${pt.y}`;
              }).join(' ');

              return (
                <svg viewBox="0 0 300 240" className="w-full max-w-[320px] h-auto overflow-visible select-none">
                  {/* Concentric Grid Rings */}
                  {rings.map((ringFrac, idx) => {
                    const pts = angles.map(a => {
                      const pt = getCoord(a, R * ringFrac);
                      return `${pt.x},${pt.y}`;
                    }).join(' ');
                    return (
                      <polygon
                        key={idx}
                        points={pts}
                        fill="none"
                        stroke="#1E293B"
                        strokeWidth="1"
                      />
                    );
                  })}

                  {/* Radial Axis Lines */}
                  {angles.map((a, idx) => {
                    const pt = getCoord(a, R);
                    return (
                      <line
                        key={idx}
                        x1={cx}
                        y1={cy}
                        x2={pt.x}
                        y2={pt.y}
                        stroke="#1E293B"
                        strokeWidth="1"
                      />
                    );
                  })}

                  {/* Grid Scale Numbers along bottom-right axis */}
                  {[25, 50, 75, 100].map((val) => {
                    const pt = getCoord(angles[1], R * (val / 100));
                    return (
                      <text
                        key={val}
                        x={pt.x + 3}
                        y={pt.y - 2}
                        fill="#475569"
                        fontSize="8"
                        fontFamily="monospace"
                      >
                        {val}
                      </text>
                    );
                  })}

                  {/* Target 80% Ring (Dashed Cyan) */}
                  <polygon
                    points={targetPoints}
                    fill="none"
                    stroke="#2DD4BF"
                    strokeWidth="1.5"
                    strokeDasharray="4 3"
                  />

                  {/* User Mastery Polygon (Yellow with translucent fill) */}
                  <polygon
                    points={userPoints}
                    fill="rgba(234, 179, 8, 0.22)"
                    stroke="#EAB308"
                    strokeWidth="2.5"
                  />

                  {/* User Vertex Marker Circles */}
                  {angles.map((a, i) => {
                    const scoreFrac = Math.max(0.12, Math.min(1.0, userAccs[i] / 100));
                    const pt = getCoord(a, R * scoreFrac);
                    return (
                      <circle
                        key={i}
                        cx={pt.x}
                        cy={pt.y}
                        r="4"
                        fill="#FACC15"
                        stroke="#0F172A"
                        strokeWidth="1.5"
                      />
                    );
                  })}

                  {/* Domain Vertex Labels */}
                  <text
                    x={cx}
                    y={cy - R - 10}
                    textAnchor="middle"
                    fill="#94A3B8"
                    fontSize="11"
                    fontWeight="600"
                  >
                    Plan & Manage
                  </text>

                  <text
                    x={cx + R * Math.cos(angles[1]) + 8}
                    y={cy + R * Math.sin(angles[1]) + 14}
                    textAnchor="start"
                    fill="#94A3B8"
                    fontSize="11"
                    fontWeight="600"
                  >
                    Prepare & Connect
                  </text>

                  <text
                    x={cx + R * Math.cos(angles[2]) - 8}
                    y={cy + R * Math.sin(angles[2]) + 14}
                    textAnchor="end"
                    fill="#94A3B8"
                    fontSize="11"
                    fontWeight="600"
                  >
                    Model & Explore
                  </text>
                </svg>
              );
            })()}
          </div>

          <div className="text-center text-xs text-slate-400 pt-3 border-t border-slate-800/60 flex items-center justify-center gap-5">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
              Your Mastery
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3.5 h-0.5 border-b border-dashed border-teal-400"></span>
              Exam Target (80%)
            </span>
          </div>
        </div>

        {/* Right: Recent Exam Attempts */}
        <div className="lg:col-span-7 bg-[#10172A] border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-white">Recent Exam Attempts</h3>
            <button
              onClick={() => setActiveTab('analytics')}
              className="text-xs font-bold text-teal-400 hover:text-teal-300 flex items-center gap-1 transition-colors"
            >
              <span>View Full Telemetry</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Attempts List */}
          <div className="space-y-3 flex-1 flex flex-col justify-center">
            {stats.examAttempts && stats.examAttempts.length > 0 ? (
              stats.examAttempts.slice(0, 3).map((attempt, idx) => {
                const percentage = Math.round((attempt.correctCount / attempt.totalQuestions) * 100);
                const minutesSpent = Math.max(1, Math.round(attempt.timeSpentSeconds / 60));
                const formattedDate = (() => {
                  try {
                    const d = new Date(attempt.timestamp);
                    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + 
                      ', ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
                  } catch {
                    return attempt.timestamp;
                  }
                })();

                return (
                  <div
                    key={attempt.id || idx}
                    onClick={() => onSelectAttempt ? onSelectAttempt(attempt) : setActiveTab('results')}
                    className="p-3.5 sm:p-4 rounded-xl bg-slate-900/70 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 cursor-pointer transition-all flex items-center justify-between group"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border ${
                        attempt.passed 
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                          : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      }`}>
                        <CheckCircle2 className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-xs sm:text-sm font-bold text-white tracking-wide">
                            {attempt.totalQuestions <= 25 ? '7-DAY STUDY EXAM' : 'FULL MOCK EXAM'}
                          </span>
                          <span className={`text-[9px] sm:text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                            attempt.passed 
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' 
                              : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          }`}>
                            {attempt.passed ? 'PASSED' : 'FAILED'}
                          </span>
                        </div>
                        <div className="text-[11px] sm:text-xs text-slate-400">
                          {formattedDate} • {attempt.totalQuestions} questions • ~{minutesSpent}m spent
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 sm:gap-4 text-right">
                      <div>
                        <div className="text-lg sm:text-2xl font-black text-white">{percentage}%</div>
                        <div className="text-[10px] sm:text-[11px] text-slate-400">
                          {attempt.correctCount}/{attempt.totalQuestions} correct
                        </div>
                      </div>
                      <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-transform group-hover:translate-x-1 shrink-0" />
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="py-8 px-4 text-center rounded-xl bg-slate-900/40 border border-dashed border-slate-800">
                <Target className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <p className="text-sm font-semibold text-slate-300 mb-1">No exam attempts recorded yet</p>
                <p className="text-xs text-slate-500 mb-4 max-w-sm mx-auto">
                  Take your first timed mock exam to test readiness and generate historical progression telemetry.
                </p>
                <button
                  onClick={() => setActiveTab('mock-exam')}
                  className="px-4 py-2 rounded-xl bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 border border-teal-500/30 text-xs font-bold inline-flex items-center gap-1.5 transition-all"
                >
                  <PlayCircle className="w-4 h-4" />
                  <span>Start Full Mock Exam</span>
                </button>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* 7-Day Intensive Exam Countdown Plan */}
      <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-amber-400" />
              7-Day Intensive Certification Roadmap
            </h2>
            <p className="text-xs text-slate-400">Structured day-by-day revision plan designed for your 2-week exam timeline</p>
          </div>
          <button
            onClick={() => setActiveTab('study-guides')}
            className="text-xs text-teal-400 hover:text-teal-300 flex items-center gap-1 font-semibold"
          >
            <span>View All Cheat Sheets</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-3">
          {[
            { day: 'Day 1', title: 'Workspaces & CU Admin', domain: 'domain1' as DomainId, tag: 'Smoothing' },
            { day: 'Day 2', title: 'OneLake Shortcuts', domain: 'domain2' as DomainId, tag: 'ADLS & S3' },
            { day: 'Day 3', title: 'Delta Lake & V-Order', domain: 'domain2' as DomainId, tag: 'OPTIMIZE' },
            { day: 'Day 4', title: 'PySpark & Ingestion', domain: 'domain2' as DomainId, tag: 'Dataflows Gen2' },
            { day: 'Day 5', title: 'Direct Lake Modeling', domain: 'domain3' as DomainId, tag: 'Fallbacks' },
            { day: 'Day 6', title: 'DAX & Calc Groups', domain: 'domain3' as DomainId, tag: 'Tabular Editor' },
            { day: 'Day 7', title: 'Full 100m Mock Exam', domain: 'mock' as any, tag: 'Scorecard' }
          ].map((item, idx) => (
            <div
              key={idx}
              onClick={() => {
                if (item.domain === 'mock') setActiveTab('mock-exam');
                else onFilterDomain(item.domain);
              }}
              className="bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 rounded-xl p-3 cursor-pointer transition-all hover:border-teal-500/50 flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-bold text-teal-400 group-hover:text-teal-300">{item.day}</span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">{item.tag}</span>
                </div>
                <h4 className="text-xs font-semibold text-slate-200 group-hover:text-white mb-2 leading-tight">
                  {item.title}
                </h4>
              </div>
              <span className="text-[10px] text-slate-500 group-hover:text-teal-400 flex items-center gap-0.5">
                Start Review →
              </span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
