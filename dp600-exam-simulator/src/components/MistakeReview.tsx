import React, { useState } from 'react';
import { Question, UserStats, DOMAINS } from '../types';
import { storageService } from '../services/storageService';
import { StepOrderingQuestion } from './StepOrderingQuestion';
import { 
  Bookmark, 
  RotateCcw, 
  Trash2, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Lightbulb, 
  HelpCircle, 
  Star, 
  ExternalLink, 
  Code2, 
  Sparkles,
  ArrowRight,
  BookOpen
} from 'lucide-react';

interface MistakeReviewProps {
  questions: Question[];
  stats: UserStats;
  onDrillMistakes: (questionIds: string[]) => void;
  onStatsChange: () => void;
  onStartPractice: () => void;
}

export const MistakeReview: React.FC<MistakeReviewProps> = ({
  questions,
  stats,
  onDrillMistakes,
  onStatsChange,
  onStartPractice
}) => {
  const [expandedExplanations, setExpandedExplanations] = useState<Record<string, boolean>>({});
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [activeLang, setActiveLang] = useState<'EN' | 'FR'>('EN');

  // Filter questions that were answered incorrectly
  const mistakeQuestions = questions.filter(q => {
    const attempt = stats.answeredQuestionIds[q.id];
    return attempt && !attempt.isCorrect;
  });

  const toggleExplanation = (qId: string) => {
    setExpandedExplanations(prev => ({
      ...prev,
      [qId]: !prev[qId]
    }));
  };

  const handleSelectOption = (q: Question, optId: string) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [q.id]: optId
    }));

    const isCorrect = q.type === 'drag_and_drop'
      ? JSON.stringify(q.correctOrder) === optId
      : optId === q.correctOptionId;

    storageService.recordAnswer(q.id, optId, isCorrect);
    onStatsChange();

    // Auto expand explanation on attempt
    setExpandedExplanations(prev => ({
      ...prev,
      [q.id]: true
    }));
  };

  const handleToggleBookmark = (qId: string) => {
    storageService.toggleBookmark(qId);
    onStatsChange();
  };

  const handleResetData = () => {
    if (window.confirm('Are you sure you want to reset your mistake history?')) {
      storageService.resetMistakes();
      onStatsChange();
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-20 animate-fade-in text-white">
      
      {/* Top Banner Header matching Reference Screenshot 3 */}
      <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-6 relative overflow-hidden">
        <div className="space-y-1.5 relative z-10">
          <div className="flex items-center gap-2">
            <Bookmark className="w-5 h-5 text-rose-500 fill-rose-500/20" />
            <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight">
              Mistake Review & Weak Point Analysis
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-300">
            Revisit all questions previously answered incorrectly to master difficult concepts.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 relative z-10 shrink-0">
          {mistakeQuestions.length > 0 && (
            <button
              onClick={() => onDrillMistakes(mistakeQuestions.map(q => q.id))}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 text-xs sm:text-sm font-bold shadow-lg shadow-amber-500/20 transition-all active:scale-95"
            >
              <RotateCcw className="w-4 h-4 text-slate-950" />
              <span>Drill All Mistakes ({mistakeQuestions.length})</span>
            </button>
          )}

          <button
            onClick={handleResetData}
            className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs sm:text-sm font-medium text-slate-400 hover:text-rose-400 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span>Reset Data</span>
          </button>
        </div>
      </div>

      {/* Empty State when no mistakes exist */}
      {mistakeQuestions.length === 0 ? (
        <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-12 text-center space-y-4 shadow-xl">
          <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto text-emerald-400">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-white">No Missed Questions Recorded</h3>
            <p className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto">
              You haven't made any mistakes yet or all previous mistakes have been resolved. Complete a Timed Mock Exam or Practice session to challenge your skills!
            </p>
          </div>
          <div className="pt-2">
            <button
              onClick={onStartPractice}
              className="px-5 py-2.5 rounded-xl bg-teal-500/20 hover:bg-teal-500/30 text-teal-300 border border-teal-500/40 text-xs sm:text-sm font-semibold transition-all inline-flex items-center gap-2"
            >
              <BookOpen className="w-4 h-4" />
              <span>Start Interactive Practice Mode</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {mistakeQuestions.map((q) => {
            const attemptInfo = stats.answeredQuestionIds[q.id];
            const isBookmarked = stats.bookmarkedQuestionIds.includes(q.id);
            const isExpanded = !!expandedExplanations[q.id];
            const userAnswer = selectedAnswers[q.id] || attemptInfo?.answeredOptionId;
            const attemptCount = attemptInfo?.attemptCount || 1;
            const correctCount = attemptInfo?.correctCount || 0;

            const domainLabel = DOMAINS[q.domain]?.name || q.domain;

            return (
              <div key={q.id} className="space-y-1.5">
                
                {/* Attempt Status Banner */}
                <div className="flex items-center justify-between text-xs px-2 text-rose-400 font-medium">
                  <div className="flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                    <span>Attempted {attemptCount} {attemptCount === 1 ? 'time' : 'times'} • {correctCount} correct</span>
                  </div>
                  <span className="text-slate-500 text-[11px]">
                    Last attempt: {attemptInfo?.lastAttemptDate || 'Recent'}
                  </span>
                </div>

                {/* Question Card matching PL-300 Screenshot 3 */}
                <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-xl space-y-4">
                  
                  {/* Meta Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-slate-800/80">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                        {q.id}
                      </span>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-300 border border-teal-500/20">
                        {domainLabel}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        q.difficulty === 'Easy' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                        q.difficulty === 'Medium' ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20' :
                        'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                      }`}>
                        {q.difficulty?.toUpperCase() || 'MEDIUM'}
                      </span>
                      <span className="text-[11px] text-slate-500 flex items-center gap-1">
                        ~50s
                      </span>
                    </div>

                    {/* Top Right Tool Buttons */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => toggleExplanation(q.id)}
                        className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors border ${
                          isExpanded 
                            ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' 
                            : 'bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border-amber-500/20'
                        }`}
                      >
                        <Lightbulb className="w-3.5 h-3.5" />
                        <span>Explanation & Terms</span>
                      </button>

                      <button
                        onClick={() => setActiveLang(prev => prev === 'EN' ? 'FR' : 'EN')}
                        className="flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 font-semibold"
                        title="Toggle French/English"
                      >
                        <span>{activeLang === 'EN' ? '🇫🇷 Français' : '🇬🇧 English'}</span>
                      </button>

                      <button
                        onClick={() => handleToggleBookmark(q.id)}
                        className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors border ${
                          isBookmarked 
                            ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' 
                            : 'bg-slate-900 hover:bg-slate-800 text-slate-400 border-slate-800'
                        }`}
                      >
                        <Star className={`w-3.5 h-3.5 ${isBookmarked ? 'fill-amber-400 text-amber-400' : ''}`} />
                        <span>{isBookmarked ? 'Saved' : 'Save'}</span>
                      </button>
                    </div>
                  </div>

                  {/* Topic Breadcrumb */}
                  <div className="flex items-center gap-1.5 text-xs text-amber-400/90 font-medium">
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>{q.topic}</span>
                  </div>

                  {/* Question Stem */}
                  <p className="text-sm sm:text-base font-semibold text-white leading-relaxed">
                    {q.text}
                  </p>

                  {/* Code snippet if any */}
                  {q.codeSnippet && (
                    <div className="rounded-xl overflow-hidden border border-slate-800 bg-[#090D17] text-xs">
                      <div className="bg-slate-900/80 px-3 py-1.5 border-b border-slate-800 flex items-center justify-between text-slate-400 text-[11px]">
                        <span className="font-mono uppercase">{q.codeSnippet.language}</span>
                        <Code2 className="w-3.5 h-3.5" />
                      </div>
                      <pre className="p-3 text-slate-200 font-mono overflow-x-auto leading-relaxed">
                        <code>{q.codeSnippet.code}</code>
                      </pre>
                    </div>
                  )}

                  {/* Question Interaction: Drag & Drop vs Multiple Choice */}
                  {q.type === 'drag_and_drop' && q.orderingSteps && q.correctOrder ? (
                    <div className="pt-2">
                      <StepOrderingQuestion
                        question={q}
                        isAnswerRevealed={isExpanded || !!userAnswer}
                        onAnswerSubmit={(orderedIds) => handleSelectOption(q, JSON.stringify(orderedIds))}
                        savedAnswer={userAnswer}
                      />
                    </div>
                  ) : (
                    <div className="space-y-2 pt-1">
                      {q.options.map((opt) => {
                        const isSelected = userAnswer === opt.id;
                        const isCorrectOption = opt.id === q.correctOptionId;
                        
                        let optStyle = 'border-slate-800 hover:border-slate-700 bg-slate-900/60 text-slate-300';
                        if (userAnswer) {
                          if (isCorrectOption) {
                            optStyle = 'border-emerald-500/50 bg-emerald-500/10 text-emerald-200 font-medium';
                          } else if (isSelected) {
                            optStyle = 'border-rose-500/50 bg-rose-500/10 text-rose-200';
                          }
                        }

                        return (
                          <button
                            key={opt.id}
                            onClick={() => handleSelectOption(q, opt.id)}
                            className={`w-full text-left p-3.5 rounded-xl border text-xs sm:text-sm flex items-start gap-3 transition-all ${optStyle}`}
                          >
                            <span className="w-6 h-6 rounded-lg bg-slate-800 text-slate-300 border border-slate-700/60 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                              {opt.id}
                            </span>
                            <span className="flex-1 leading-relaxed">
                              {opt.text}
                            </span>
                            {userAnswer && isCorrectOption && (
                              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                            )}
                            {userAnswer && isSelected && !isCorrectOption && (
                              <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {/* Expandable Explanation Section */}
                  {isExpanded && (
                    <div className="pt-4 border-t border-slate-800 space-y-3 animate-fade-in">
                      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
                        <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-teal-400">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          <span>Detailed Explanation</span>
                        </div>
                        <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">
                          {q.explanation}
                        </p>
                      </div>

                      {q.msLearnUrl && (
                        <div className="flex justify-end">
                          <a
                            href={q.msLearnUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1.5 text-xs text-sky-400 hover:text-sky-300 font-semibold bg-slate-900 hover:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-800 transition-colors"
                          >
                            <span>Learn More: {q.msLearnTitle || 'Microsoft Fabric Documentation'}</span>
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        </div>
                      )}
                    </div>
                  )}

                </div>

              </div>
            );
          })}
        </div>
      )}

    </div>
  );
};
