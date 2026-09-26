import React, { useEffect, useState } from 'react';
import { ExamAttempt, Question, DOMAINS, DomainId } from '../types';
import confetti from 'canvas-confetti';
import { 
  Award, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Target, 
  AlertTriangle, 
  ArrowRight, 
  RotateCcw, 
  Layers, 
  ExternalLink,
  Filter
} from 'lucide-react';
import { ActiveTab } from './Navbar';

interface ExamResultsProps {
  attempt: ExamAttempt;
  questions: Question[];
  setActiveTab: (tab: ActiveTab) => void;
  onRetakeExam: () => void;
  onDrillWeakTopic: (topic: string) => void;
}

export const ExamResults: React.FC<ExamResultsProps> = ({
  attempt,
  questions,
  setActiveTab,
  onRetakeExam,
  onDrillWeakTopic
}) => {
  const [reviewFilter, setReviewFilter] = useState<'all' | 'correct' | 'incorrect' | 'flagged'>('all');

  // Trigger confetti on pass
  useEffect(() => {
    if (attempt.passed) {
      confetti({
        particleCount: 120,
        spread: 70,
        origin: { y: 0.6 }
      });
    }
  }, [attempt.passed]);

  const examQuestions = attempt.questionIds
    .map(id => questions.find(q => q.id === id))
    .filter((q): q is Question => q !== undefined);

  const filteredReviewQuestions = examQuestions.filter(q => {
    const userAnswer = attempt.userAnswers[q.id];
    const isCorrect = userAnswer === q.correctOptionId;
    const isFlagged = attempt.flaggedQuestionIds.includes(q.id);

    if (reviewFilter === 'correct') return isCorrect;
    if (reviewFilter === 'incorrect') return !isCorrect;
    if (reviewFilter === 'flagged') return isFlagged;
    return true;
  });

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16 animate-fade-in text-white">
      
      {/* Score Banner */}
      <div className={`rounded-3xl p-6 sm:p-8 border shadow-2xl relative overflow-hidden ${
        attempt.passed
          ? 'bg-gradient-to-br from-[#0F291E] via-[#0D1F2D] to-[#0A1628] border-emerald-500/30'
          : 'bg-gradient-to-br from-[#2D1217] via-[#1F1322] to-[#0E1526] border-rose-500/30'
      }`}>
        <div className="flex flex-col md:flex-row items-center justify-between gap-6 relative z-10">
          
          <div className="text-center md:text-left space-y-2">
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
              attempt.passed
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
            }`}>
              {attempt.passed ? '✓ Passing Score Achieved' : '⚠️ Certification Retest Needed'}
            </span>

            <h1 className="text-2xl sm:text-4xl font-extrabold text-white">
              {attempt.passed ? 'Congratulations! You Passed the Mock Exam' : 'Keep Pushing! You Are Close to Passing'}
            </h1>
            <p className="text-sm text-slate-300 max-w-xl">
              {attempt.passed
                ? 'Your performance demonstrates readiness for the Microsoft Certified Fabric Analytics Engineer Associate (DP-600) exam.'
                : 'Review the domain diagnostic and weak topics below to focus your remaining study time before the official exam.'}
            </p>
          </div>

          {/* Big Score Card */}
          <div className="bg-[#0B101D]/80 backdrop-blur-md rounded-2xl border border-slate-700/80 p-6 flex flex-col items-center justify-center text-center shadow-2xl shrink-0 min-w-[220px]">
            <div className="text-xs uppercase font-bold text-slate-400 tracking-wider mb-1">Final Score</div>
            <div className={`text-5xl font-black tracking-tight ${
              attempt.passed ? 'text-emerald-400' : 'text-rose-400'
            }`}>
              {attempt.score}
            </div>
            <div className="text-xs text-slate-400 mt-1">Passing mark: 700 / 1000</div>

            <div className="mt-4 pt-3 border-t border-slate-800 w-full flex items-center justify-between text-xs text-slate-300">
              <span>Status:</span>
              <span className={`font-bold ${attempt.passed ? 'text-emerald-400' : 'text-rose-400'}`}>
                {attempt.passed ? 'PASS' : 'FAIL'}
              </span>
            </div>
          </div>

        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center">
            <Target className="w-5 h-5 text-teal-400" />
          </div>
          <div>
            <div className="text-xl font-bold text-white">
              {Math.round((attempt.correctCount / attempt.totalQuestions) * 100)}%
            </div>
            <div className="text-xs text-slate-400">Exam Accuracy</div>
          </div>
        </div>

        <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <div className="text-xl font-bold text-white">
              {attempt.correctCount} / {attempt.totalQuestions}
            </div>
            <div className="text-xs text-slate-400">Correct Answers</div>
          </div>
        </div>

        <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center">
            <Clock className="w-5 h-5 text-sky-400" />
          </div>
          <div>
            <div className="text-xl font-bold text-white">
              {formatDuration(attempt.timeSpentSeconds)}
            </div>
            <div className="text-xs text-slate-400">Time Taken</div>
          </div>
        </div>

        <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
            <Award className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <div className="text-xl font-bold text-white">{attempt.flaggedQuestionIds.length}</div>
            <div className="text-xs text-slate-400">Flagged Questions</div>
          </div>
        </div>
      </div>

      {/* Domain Breakdown & Weak Topics Diagnostic */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Domain Progress Bars */}
        <div className="lg:col-span-2 bg-[#10172A] border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-teal-400" />
              Domain Proficiency Breakdown
            </h2>
            <span className="text-xs text-slate-400">Official Weighting</span>
          </div>

          <div className="space-y-4 pt-1">
            {(Object.keys(attempt.domainScores) as DomainId[]).map((domId) => {
              const score = attempt.domainScores[domId];
              const info = DOMAINS[domId];
              const isPassing = score.percentage >= 70;

              return (
                <div key={domId} className="space-y-1.5 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/80">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-white">
                      {info.code}: {info.name} ({info.percentage})
                    </span>
                    <span className={`font-bold ${isPassing ? 'text-teal-400' : 'text-amber-400'}`}>
                      {score.correct}/{score.total} ({score.percentage}%)
                    </span>
                  </div>

                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isPassing ? 'bg-teal-400' : 'bg-amber-400'
                      }`}
                      style={{ width: `${score.percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Weak Topics Diagnostic Card */}
        <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-6 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center gap-2 text-rose-400 mb-2">
              <AlertTriangle className="w-5 h-5" />
              <h2 className="text-base font-bold text-white">Targeted Weak Topics</h2>
            </div>
            <p className="text-xs text-slate-400 mb-3">
              Topics scoring under 70% accuracy. Drill these specifically to guarantee your pass mark.
            </p>

            {attempt.weakTopics.length === 0 ? (
              <div className="bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-xl text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Outstanding! No critical weak areas detected.</span>
              </div>
            ) : (
              <div className="space-y-2">
                {attempt.weakTopics.map((topic, i) => (
                  <div
                    key={i}
                    onClick={() => onDrillWeakTopic(topic)}
                    className="bg-slate-900/80 hover:bg-slate-800 p-2.5 rounded-xl border border-slate-800 hover:border-teal-500/50 cursor-pointer flex items-center justify-between transition-all group"
                  >
                    <span className="text-xs text-slate-200 group-hover:text-white font-medium">{topic}</span>
                    <span className="text-[10px] text-teal-400 flex items-center gap-0.5">
                      Drill →
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-2 pt-2 border-t border-slate-800">
            <button
              onClick={onRetakeExam}
              className="w-full py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              Retake Mock Exam
            </button>
            <button
              onClick={() => setActiveTab('dashboard')}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-medium text-xs transition-colors"
            >
              Return to Dashboard
            </button>
          </div>
        </div>

      </div>

      {/* Question-By-Question Detailed Review */}
      <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-white">Full Exam Question Review</h2>
            <p className="text-xs text-slate-400">Detailed explanation and answer verification for every question</p>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
            <button
              onClick={() => setReviewFilter('all')}
              className={`px-3 py-1 rounded-lg transition-colors ${
                reviewFilter === 'all' ? 'bg-teal-500 text-white font-semibold' : 'text-slate-400 hover:text-white'
              }`}
            >
              All ({examQuestions.length})
            </button>
            <button
              onClick={() => setReviewFilter('incorrect')}
              className={`px-3 py-1 rounded-lg transition-colors ${
                reviewFilter === 'incorrect' ? 'bg-rose-500 text-white font-semibold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Incorrect ({attempt.totalQuestions - attempt.correctCount})
            </button>
            <button
              onClick={() => setReviewFilter('correct')}
              className={`px-3 py-1 rounded-lg transition-colors ${
                reviewFilter === 'correct' ? 'bg-emerald-500 text-white font-semibold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Correct ({attempt.correctCount})
            </button>
          </div>
        </div>

        {/* Question Cards List */}
        <div className="space-y-4">
          {filteredReviewQuestions.map((q, idx) => {
            const userAnswer = attempt.userAnswers[q.id];
            const isCorrect = userAnswer === q.correctOptionId;

            return (
              <div
                key={q.id}
                className={`p-5 rounded-2xl border transition-all ${
                  isCorrect
                    ? 'bg-slate-900/50 border-slate-800/80'
                    : 'bg-rose-500/[0.04] border-rose-500/20'
                }`}
              >
                <div className="flex items-center justify-between mb-3 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-400">Q{idx + 1}</span>
                    <span className="text-teal-400 font-semibold">{DOMAINS[q.domain].code}</span>
                    <span className="text-slate-400">• {q.topic}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    {isCorrect ? (
                      <span className="flex items-center gap-1 text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 text-[11px]">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Correct ({q.correctOptionId})
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-rose-400 font-bold bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20 text-[11px]">
                        <XCircle className="w-3.5 h-3.5" />
                        Incorrect (You chose {userAnswer || 'None'}, Correct: {q.correctOptionId})
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-sm font-medium text-slate-200 mb-3">{q.text}</p>

                {/* Explanation */}
                <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80 text-xs text-slate-300 leading-relaxed space-y-2">
                  <div className="font-bold text-teal-400">Explanation:</div>
                  <p>{q.explanation}</p>

                  {q.msLearnUrl && (
                    <div className="pt-2 border-t border-slate-800">
                      <a
                        href={q.msLearnUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sky-400 hover:text-sky-300 font-semibold inline-flex items-center gap-1 text-[11px]"
                      >
                        <span>Learn more on Microsoft Learn</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

      </div>

    </div>
  );
};
