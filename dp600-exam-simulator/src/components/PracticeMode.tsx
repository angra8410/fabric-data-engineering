import React, { useState, useMemo } from 'react';
import { Question, DomainId, DOMAINS, UserStats } from '../types';
import { storageService } from '../services/storageService';
import { CASE_STUDIES } from '../data/caseStudies';
import { CaseStudyModal } from './CaseStudyModal';
import { MSLearnDrawer } from './MSLearnDrawer';
import { StepOrderingQuestion } from './StepOrderingQuestion';
import { 
  Bookmark, 
  BookmarkCheck, 
  CheckCircle2, 
  XCircle, 
  ArrowLeft, 
  ArrowRight, 
  Shuffle, 
  BookOpen, 
  Layers, 
  ExternalLink,
  Code2, 
  Filter, 
  ListOrdered, 
  CheckSquare,
  Lightbulb,
  HelpCircle,
  Star
} from 'lucide-react';

interface PracticeModeProps {
  questions: Question[];
  stats: UserStats;
  onStatsChange: () => void;
  initialDomainFilter?: DomainId | 'all';
  initialQuestionId?: string;
}

export const PracticeMode: React.FC<PracticeModeProps> = ({
  questions,
  stats,
  onStatsChange,
  initialDomainFilter = 'all',
  initialQuestionId
}) => {
  const [selectedDomain, setSelectedDomain] = useState<DomainId | 'all'>(
    initialQuestionId ? 'all' : initialDomainFilter
  );
  const [selectedTopic, setSelectedTopic] = useState<string>('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'unanswered' | 'incorrect' | 'bookmarked'>('all');
  const [activeLang, setActiveLang] = useState<'EN' | 'FR'>('EN');

  // Session score tracker
  const [sessionTotal, setSessionTotal] = useState<number>(0);
  const [sessionCorrect, setSessionCorrect] = useState<number>(0);

  const initialIndex = useMemo(() => {
    if (!initialQuestionId) return 0;
    const idx = questions.findIndex(q => q.id === initialQuestionId);
    return idx >= 0 ? idx : 0;
  }, [questions, initialQuestionId]);

  const [currentIndex, setCurrentIndex] = useState<number>(initialIndex);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [selectedMulti, setSelectedMulti] = useState<string[]>([]);
  const [isAnswerRevealed, setIsAnswerRevealed] = useState<boolean>(false);
  const [showCaseStudy, setShowCaseStudy] = useState<boolean>(false);
  const [showMSLearn, setShowMSLearn] = useState<boolean>(false);

  // Sync index if initialQuestionId changes
  React.useEffect(() => {
    if (initialQuestionId) {
      setSelectedDomain('all');
      setSelectedTopic('all');
      setSelectedDifficulty('all');
      setSelectedStatus('all');
      const idx = questions.findIndex(q => q.id === initialQuestionId);
      if (idx >= 0) setCurrentIndex(idx);
    }
  }, [initialQuestionId, questions]);

  // Extract available topics dynamically for selected domain
  const availableTopics = useMemo(() => {
    const domainQuestions = selectedDomain === 'all'
      ? questions
      : questions.filter(q => q.domain === selectedDomain);
    const topicsSet = new Set<string>();
    domainQuestions.forEach(q => {
      if (q.topic) topicsSet.add(q.topic);
    });
    return Array.from(topicsSet).sort();
  }, [questions, selectedDomain]);

  // Filtered Questions
  const filteredQuestions = useMemo(() => {
    return questions.filter(q => {
      if (selectedDomain !== 'all' && q.domain !== selectedDomain) return false;
      if (selectedTopic !== 'all' && q.topic !== selectedTopic) return false;
      if (selectedDifficulty !== 'all' && q.difficulty !== selectedDifficulty) return false;

      const attempt = stats.answeredQuestionIds[q.id];
      const isBookmarked = stats.bookmarkedQuestionIds.includes(q.id);

      if (selectedStatus === 'unanswered' && attempt) return false;
      if (selectedStatus === 'incorrect' && (!attempt || attempt.isCorrect)) return false;
      if (selectedStatus === 'bookmarked' && !isBookmarked) return false;

      return true;
    });
  }, [questions, selectedDomain, selectedTopic, selectedDifficulty, selectedStatus, stats]);

  // Safe current question
  const currentQuestion = filteredQuestions[currentIndex] || filteredQuestions[0];
  const isMulti = currentQuestion?.type === 'multi_select' || (currentQuestion?.correctOptionIds && currentQuestion.correctOptionIds.length > 1);
  const selectCount = currentQuestion?.selectCount || currentQuestion?.correctOptionIds?.length || 2;

  const handleSelectOption = (optId: string) => {
    if (!currentQuestion) return;
    setSelectedOption(optId);
    setIsAnswerRevealed(true);

    const isCorrect = currentQuestion.type === 'drag_and_drop'
      ? JSON.stringify(currentQuestion.correctOrder) === optId
      : optId === currentQuestion.correctOptionId;

    setSessionTotal(prev => prev + 1);
    if (isCorrect) setSessionCorrect(prev => prev + 1);

    storageService.recordAnswer(currentQuestion.id, optId, isCorrect);
    onStatsChange();
  };

  const handleToggleMultiOption = (optId: string) => {
    if (isAnswerRevealed) return;
    setSelectedMulti(prev => {
      if (prev.includes(optId)) {
        return prev.filter(id => id !== optId);
      }
      if (prev.length >= selectCount) {
        return [...prev.slice(1), optId];
      }
      return [...prev, optId];
    });
  };

  const handleCheckMultiAnswer = () => {
    if (!currentQuestion || selectedMulti.length === 0) return;
    const sortedSelected = [...selectedMulti].sort();
    const sortedCorrect = [...(currentQuestion.correctOptionIds || [currentQuestion.correctOptionId])].sort();
    const isCorrect = JSON.stringify(sortedSelected) === JSON.stringify(sortedCorrect);

    setSelectedOption(JSON.stringify(sortedSelected));
    setIsAnswerRevealed(true);

    setSessionTotal(prev => prev + 1);
    if (isCorrect) setSessionCorrect(prev => prev + 1);

    storageService.recordAnswer(currentQuestion.id, JSON.stringify(sortedSelected), isCorrect);
    onStatsChange();
  };

  const handleToggleBookmark = () => {
    if (!currentQuestion) return;
    storageService.toggleBookmark(currentQuestion.id);
    onStatsChange();
  };

  const resetQuestionState = () => {
    setSelectedOption(null);
    setSelectedMulti([]);
    setIsAnswerRevealed(false);
  };

  const goToNext = () => {
    if (currentIndex < filteredQuestions.length - 1) {
      setCurrentIndex(currentIndex + 1);
      resetQuestionState();
    }
  };

  const goToPrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      resetQuestionState();
    }
  };

  const goToRandom = () => {
    if (filteredQuestions.length > 1) {
      const randomIndex = Math.floor(Math.random() * filteredQuestions.length);
      setCurrentIndex(randomIndex);
      resetQuestionState();
    }
  };

  const currentCaseStudy = currentQuestion?.caseStudyId 
    ? CASE_STUDIES.find(cs => cs.id === currentQuestion.caseStudyId)
    : undefined;

  const isBookmarked = currentQuestion ? stats.bookmarkedQuestionIds.includes(currentQuestion.id) : false;
  const domainLabel = currentQuestion ? DOMAINS[currentQuestion.domain]?.name || currentQuestion.domain : '';

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20 animate-fade-in text-white">
      
      {/* Header Banner matching Screenshot 4 */}
      <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-amber-400" />
            <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight">
              Interactive Practice Mode
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-300">
            Immediate feedback with step-by-step technical explanations and Fabric breakdowns.
          </p>
        </div>

        {/* Session Stats Badge */}
        <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 shrink-0">
          <span>Session: <strong className="text-emerald-400">{sessionCorrect}</strong> / <strong>{sessionTotal}</strong> Correct</span>
        </div>
      </div>

      {/* 3-Dropdown Filter Row matching Screenshot 4 */}
      <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-lg space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          
          {/* 1. Filter by Domain */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">Filter by Domain:</label>
            <select
              value={selectedDomain}
              onChange={(e) => {
                setSelectedDomain(e.target.value as any);
                setSelectedTopic('all');
                setCurrentIndex(0);
                resetQuestionState();
              }}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-teal-400 cursor-pointer"
            >
              <option value="all">All Domains ({questions.length} Qs)</option>
              <option value="domain1">Domain 1: Plan & Manage (10-15%)</option>
              <option value="domain2">Domain 2: Prepare & Connect (40-45%)</option>
              <option value="domain3">Domain 3: Model & Explore (40-45%)</option>
            </select>
          </div>

          {/* 2. Filter by Topic */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">Filter by Topic:</label>
            <select
              value={selectedTopic}
              onChange={(e) => {
                setSelectedTopic(e.target.value);
                setCurrentIndex(0);
                resetQuestionState();
              }}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-teal-400 cursor-pointer"
            >
              <option value="all">All Topics in Domain</option>
              {availableTopics.map(topic => (
                <option key={topic} value={topic}>{topic}</option>
              ))}
            </select>
          </div>

          {/* 3. Filter by Difficulty */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">Filter by Difficulty:</label>
            <select
              value={selectedDifficulty}
              onChange={(e) => {
                setSelectedDifficulty(e.target.value);
                setCurrentIndex(0);
                resetQuestionState();
              }}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-teal-400 cursor-pointer"
            >
              <option value="all">All Difficulties</option>
              <option value="Easy">Easy</option>
              <option value="Medium">Medium</option>
              <option value="Hard">Hard</option>
            </select>
          </div>

        </div>
      </div>

      {/* Main Question Container */}
      {!currentQuestion ? (
        <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-12 text-center text-slate-400 space-y-3">
          <BookOpen className="w-12 h-12 text-slate-600 mx-auto" />
          <p className="text-base font-semibold text-white">No questions match your current filter selection.</p>
          <p className="text-xs text-slate-500">Try selecting "All Topics in Domain" or resetting your domain filter.</p>
          <button
            onClick={() => {
              setSelectedDomain('all');
              setSelectedTopic('all');
              setSelectedDifficulty('all');
              setSelectedStatus('all');
            }}
            className="px-4 py-2 rounded-xl bg-teal-500/20 hover:bg-teal-500/30 text-teal-300 border border-teal-500/40 text-xs font-semibold transition-colors inline-block"
          >
            Reset All Filters
          </button>
        </div>
      ) : (
        <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl space-y-6">
          
          {/* Top Line Meta & Action Buttons matching Screenshot 4 */}
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-bold text-white">
                Question {currentIndex + 1} <span className="text-slate-500 text-xs font-normal">of {filteredQuestions.length}</span>
              </span>
              <span className="text-xs font-mono font-bold text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                {currentQuestion.id}
              </span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20">
                {domainLabel}
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                currentQuestion.difficulty === 'Easy' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                currentQuestion.difficulty === 'Medium' ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20' :
                'bg-purple-500/10 text-purple-400 border border-purple-500/20'
              }`}>
                {currentQuestion.difficulty?.toUpperCase()}
              </span>
              <span className="text-[11px] text-slate-500">
                ~45s
              </span>
            </div>

            {/* Right Quick Actions matching Screenshot 4 */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsAnswerRevealed(prev => !prev)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 text-xs font-semibold text-amber-300 transition-colors"
                title="Toggle explanation"
              >
                <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                <span>Explanation & Terms</span>
              </button>

              <button
                onClick={() => setActiveLang(prev => prev === 'EN' ? 'FR' : 'EN')}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 font-semibold transition-colors"
                title="Toggle language"
              >
                <span>{activeLang === 'EN' ? '🇫🇷 Français' : '🇬🇧 English'}</span>
              </button>

              {currentCaseStudy && (
                <button
                  onClick={() => setShowCaseStudy(true)}
                  className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white transition-colors"
                  title="View Case Study"
                >
                  <HelpCircle className="w-4 h-4 text-sky-400" />
                </button>
              )}

              <button
                onClick={handleToggleBookmark}
                className={`p-1.5 rounded-lg border transition-colors ${
                  isBookmarked
                    ? 'bg-amber-500/20 border-amber-500/40 text-amber-400'
                    : 'bg-slate-900 hover:bg-slate-800 border-slate-800 text-slate-400 hover:text-white'
                }`}
                title={isBookmarked ? 'Remove bookmark' : 'Bookmark question'}
              >
                <Star className={`w-4 h-4 ${isBookmarked ? 'fill-amber-400 text-amber-400' : ''}`} />
              </button>
            </div>
          </div>

          {/* Breadcrumb line matching Screenshot 4 */}
          <div className="flex items-center gap-2 text-xs text-amber-400 font-medium">
            <BookOpen className="w-3.5 h-3.5" />
            <span>{domainLabel} • {currentQuestion.topic}</span>
          </div>

          {/* Question Stem */}
          <div className="space-y-4">
            <p className="text-base sm:text-lg font-bold text-white leading-relaxed">
              {currentQuestion.text}
            </p>

            {/* Code Snippet if present */}
            {currentQuestion.codeSnippet && (
              <div className="rounded-xl overflow-hidden border border-slate-800 bg-[#090D16]">
                <div className="px-4 py-1.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                  <div className="flex items-center gap-1.5">
                    <Code2 className="w-3.5 h-3.5 text-teal-400" />
                    <span>{currentQuestion.codeSnippet.language.toUpperCase()}</span>
                  </div>
                </div>
                <pre className="p-4 text-xs sm:text-sm font-mono text-teal-200 overflow-x-auto leading-relaxed">
                  <code>{currentQuestion.codeSnippet.code}</code>
                </pre>
              </div>
            )}
          </div>

          {/* Options Section: Drag & Drop Ordering OR Multi-Select OR Radio Choice */}
          {currentQuestion.type === 'drag_and_drop' ? (
            <StepOrderingQuestion
              question={currentQuestion}
              isAnswerRevealed={isAnswerRevealed}
              onAnswerSubmit={(orderedIds) => handleSelectOption(JSON.stringify(orderedIds))}
              savedAnswer={selectedOption || undefined}
            />
          ) : isMulti ? (
            <div className="space-y-4 pt-1">
              <div className="flex items-center justify-between bg-slate-900/90 border border-teal-500/30 rounded-xl px-4 py-2.5 text-xs text-teal-300">
                <div className="flex items-center gap-2 font-semibold">
                  <CheckSquare className="w-4 h-4 text-teal-400" />
                  <span>
                    Multiple Response: Select {selectCount} options ({selectedMulti.length} of {selectCount} chosen)
                  </span>
                </div>
                {!isAnswerRevealed && (
                  <button
                    onClick={handleCheckMultiAnswer}
                    disabled={selectedMulti.length === 0}
                    className="px-3.5 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 disabled:opacity-30 disabled:hover:bg-teal-500 text-white font-bold transition-all shadow-md shadow-teal-500/20 text-xs flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed"
                  >
                    <span>Check Answer</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              <div className="space-y-3">
                {currentQuestion.options.map((option) => {
                  const isSelected = selectedMulti.includes(option.id);
                  const isCorrect = (currentQuestion.correctOptionIds || [currentQuestion.correctOptionId]).includes(option.id);

                  let optionStyle = 'bg-slate-900/60 border-slate-800 hover:border-slate-600 hover:bg-slate-800/40 text-slate-200';

                  if (isAnswerRevealed) {
                    if (isCorrect) {
                      optionStyle = 'bg-emerald-500/10 border-emerald-500/60 text-emerald-200 shadow-md shadow-emerald-500/10';
                    } else if (isSelected && !isCorrect) {
                      optionStyle = 'bg-rose-500/10 border-rose-500/60 text-rose-200';
                    } else {
                      optionStyle = 'bg-slate-900/40 border-slate-800/60 text-slate-400 opacity-60';
                    }
                  } else if (isSelected) {
                    optionStyle = 'bg-teal-500/15 border-teal-500 text-teal-100 shadow-md shadow-teal-500/10';
                  }

                  return (
                    <button
                      key={option.id}
                      onClick={() => handleToggleMultiOption(option.id)}
                      disabled={isAnswerRevealed}
                      className={`w-full text-left p-4 rounded-xl border flex items-start gap-3.5 transition-all text-sm leading-relaxed ${optionStyle} ${!isAnswerRevealed ? 'cursor-pointer' : ''}`}
                    >
                      <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 border ${
                        isAnswerRevealed && isCorrect
                          ? 'bg-emerald-500 border-emerald-400 text-white'
                          : isAnswerRevealed && isSelected && !isCorrect
                          ? 'bg-rose-500 border-rose-400 text-white'
                          : isSelected
                          ? 'bg-teal-500 border-teal-400 text-white'
                          : 'bg-slate-800 border-slate-700 text-slate-300'
                      }`}>
                        {isSelected ? '✓' : option.id}
                      </div>
                      <div className="flex-1">{option.text}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            /* Single Choice Radio Options matching Screenshot 4 */
            <div className="space-y-3 pt-1">
              {currentQuestion.options.map((option) => {
                const isSelected = selectedOption === option.id;
                const isCorrect = option.id === currentQuestion.correctOptionId;

                let optionStyle = 'bg-slate-900/40 border-slate-800/90 hover:border-slate-700 hover:bg-slate-800/40 text-slate-300';

                if (isAnswerRevealed) {
                  if (isCorrect) {
                    optionStyle = 'bg-emerald-500/10 border-emerald-500/60 text-emerald-200 shadow-md shadow-emerald-500/10';
                  } else if (isSelected && !isCorrect) {
                    optionStyle = 'bg-rose-500/10 border-rose-500/60 text-rose-200';
                  } else {
                    optionStyle = 'bg-slate-900/30 border-slate-800/60 text-slate-500 opacity-60';
                  }
                } else if (isSelected) {
                  optionStyle = 'bg-teal-500/15 border-teal-500 text-teal-100 shadow-md shadow-teal-500/10';
                }

                return (
                  <button
                    key={option.id}
                    onClick={() => handleSelectOption(option.id)}
                    disabled={isAnswerRevealed}
                    className={`w-full text-left p-4 rounded-2xl border flex items-start gap-3.5 transition-all text-sm leading-relaxed ${optionStyle} ${!isAnswerRevealed ? 'cursor-pointer' : ''}`}
                  >
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 border ${
                      isAnswerRevealed && isCorrect
                        ? 'border-emerald-400 bg-emerald-500 text-white'
                        : isAnswerRevealed && isSelected && !isCorrect
                        ? 'border-rose-400 bg-rose-500 text-white'
                        : isSelected
                        ? 'border-teal-400 bg-teal-500 text-white'
                        : 'border-slate-700 bg-slate-800/80 text-slate-400'
                    }`}>
                      {isAnswerRevealed && isCorrect ? '✓' : option.id}
                    </div>

                    <div className="flex-1">
                      <span className="font-semibold mr-1">{option.id}.</span> {option.text}
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Detailed Explanation Drawer when Revealed */}
          {isAnswerRevealed && (
            <div className="pt-4 border-t border-slate-800 space-y-4 animate-fade-in">
              <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-teal-400">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Technical Explanation & Architecture</span>
                </div>
                <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">
                  {currentQuestion.explanation}
                </p>
              </div>

              {currentQuestion.msLearnUrl && (
                <div className="flex justify-end">
                  <a
                    href={currentQuestion.msLearnUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs text-sky-400 hover:text-sky-300 font-semibold bg-slate-900 hover:bg-slate-800 px-3.5 py-2 rounded-xl border border-slate-800 transition-colors"
                  >
                    <span>Official Doc: {currentQuestion.msLearnTitle || 'Microsoft Fabric Learn'}</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              )}
            </div>
          )}

          {/* Navigation Controls Footer matching Screenshot 4 */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-between gap-4">
            <button
              onClick={goToPrev}
              disabled={currentIndex === 0}
              className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 flex items-center gap-1.5 transition-colors cursor-pointer disabled:cursor-not-allowed"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Previous</span>
            </button>

            <span className="text-xs text-slate-400 font-medium">
              Question <strong className="text-white">{currentIndex + 1}</strong> of {filteredQuestions.length} available
            </span>

            <button
              onClick={goToNext}
              disabled={currentIndex >= filteredQuestions.length - 1}
              className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-slate-900 border border-slate-800 text-xs font-semibold text-teal-300 flex items-center gap-1.5 transition-colors cursor-pointer disabled:cursor-not-allowed"
            >
              <span>Next</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

        </div>
      )}

      {/* Case Study Modal */}
      {showCaseStudy && currentCaseStudy && (
        <CaseStudyModal
          caseStudy={currentCaseStudy}
          onClose={() => setShowCaseStudy(false)}
        />
      )}

      {/* MS Learn Drawer */}
      <MSLearnDrawer
        isOpen={showMSLearn}
        onClose={() => setShowMSLearn(false)}
        currentTopic={currentQuestion?.topic}
      />

    </div>
  );
};

export default PracticeMode;
