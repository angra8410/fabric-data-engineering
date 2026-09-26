import React, { useState, useEffect } from 'react';
import { Question, ExamAttempt } from '../types';
import { calculateExamScore } from '../utils/scoring';
import { storageService } from '../services/storageService';
import { CASE_STUDIES } from '../data/caseStudies';
import { CaseStudyModal } from './CaseStudyModal';
import { MSLearnDrawer } from './MSLearnDrawer';
import { StepOrderingQuestion } from './StepOrderingQuestion';
import { 
  Clock, 
  Flag, 
  Layers, 
  BookOpen, 
  ArrowLeft, 
  ArrowRight, 
  AlertTriangle, 
  CheckCircle2, 
  Send,
  Code2,
  CheckSquare
} from 'lucide-react';

interface MockExamProps {
  questions: Question[];
  onFinishExam: (attempt: ExamAttempt) => void;
  onExitExam: () => void;
}

export const MockExam: React.FC<MockExamProps> = ({
  questions,
  onFinishExam,
  onExitExam
}) => {
  const [isExamStarted, setIsExamStarted] = useState<boolean>(false);
  const [selectedQuestionCount, setSelectedQuestionCount] = useState<number>(() => Math.min(50, questions.length));
  const [selectedDuration, setSelectedDuration] = useState<number>(100);
  const [examLanguage, setExamLanguage] = useState<'EN' | 'FR'>('EN');

  const [examQuestions, setExamQuestions] = useState<Question[]>(() => {
    const shuffled = [...questions].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, Math.min(50, shuffled.length));
  });

  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [userAnswers, setUserAnswers] = useState<Record<string, string>>({});
  const [flaggedIds, setFlaggedIds] = useState<string[]>([]);
  const [timeLeftSeconds, setTimeLeftSeconds] = useState<number>(100 * 60);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [showReviewScreen, setShowReviewScreen] = useState<boolean>(false);
  const [showCaseStudy, setShowCaseStudy] = useState<boolean>(false);
  const [showMSLearn, setShowMSLearn] = useState<boolean>(false);

  const startAssessment = () => {
    const count = Math.min(selectedQuestionCount, questions.length);
    const shuffled = [...questions].sort(() => 0.5 - Math.random()).slice(0, count);
    setExamQuestions(shuffled);
    setTimeLeftSeconds(selectedDuration * 60);
    setCurrentIndex(0);
    setUserAnswers({});
    setFlaggedIds([]);
    setIsExamStarted(true);
  };

  // Timer effect
  useEffect(() => {
    if (!isExamStarted || isPaused || timeLeftSeconds <= 0) return;

    const timer = setInterval(() => {
      setTimeLeftSeconds(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          handleSubmitExam();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isExamStarted, isPaused, timeLeftSeconds]);

  const currentQuestion = examQuestions[currentIndex];
  const isFlagged = currentQuestion ? flaggedIds.includes(currentQuestion.id) : false;
  const currentCaseStudy = currentQuestion?.caseStudyId
    ? CASE_STUDIES.find(cs => cs.id === currentQuestion.caseStudyId)
    : undefined;

  const isMulti = currentQuestion?.type === 'multi_select' || (currentQuestion?.correctOptionIds && currentQuestion.correctOptionIds.length > 1);
  const selectCount = currentQuestion?.selectCount || currentQuestion?.correctOptionIds?.length || 2;

  const getSelectedOptionsForCurrent = (): string[] => {
    if (!currentQuestion) return [];
    const ans = userAnswers[currentQuestion.id];
    if (!ans) return [];
    try {
      const parsed = JSON.parse(ans);
      if (Array.isArray(parsed)) return parsed.map(String);
    } catch {}
    return ans.split(',').map(s => s.trim()).filter(Boolean);
  };

  const handleSelectOption = (optId: string) => {
    if (!currentQuestion) return;
    setUserAnswers(prev => ({ ...prev, [currentQuestion.id]: optId }));
  };

  const handleToggleMultiOption = (optId: string) => {
    if (!currentQuestion) return;
    const currentList = getSelectedOptionsForCurrent();
    let nextList: string[];
    if (currentList.includes(optId)) {
      nextList = currentList.filter(id => id !== optId);
    } else {
      if (currentList.length >= selectCount) {
        nextList = [...currentList.slice(1), optId];
      } else {
        nextList = [...currentList, optId];
      }
    }
    setUserAnswers(prev => ({
      ...prev,
      [currentQuestion.id]: JSON.stringify(nextList)
    }));
  };

  const handleToggleFlag = () => {
    if (!currentQuestion) return;
    setFlaggedIds(prev => 
      prev.includes(currentQuestion.id)
        ? prev.filter(id => id !== currentQuestion.id)
        : [...prev, currentQuestion.id]
    );
  };

  const handleSubmitExam = () => {
    const timeSpent = (selectedDuration * 60) - timeLeftSeconds;
    const attempt = calculateExamScore(examQuestions, userAnswers, timeSpent, flaggedIds);
    storageService.saveExamAttempt(attempt);
    onFinishExam(attempt);
  };

  // Format MM:SS
  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs > 0 ? hrs + ':' : ''}${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const totalAnswered = Object.keys(userAnswers).length;
  const totalUnanswered = examQuestions.length - totalAnswered;

  // 1. Assessment Configuration Screen (Screenshots 1 & 2)
  if (!isExamStarted) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 pb-20 animate-fade-in text-white">
        
        {/* Hero Header */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-amber-400 bg-amber-500/10 px-3 py-1 rounded-full border border-amber-500/20">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
              Official Exam Simulation Environment
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            DP-600 <span className="text-amber-400">Full Mock Certification Exam</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-2xl">
            A comprehensive simulation designed to reproduce the time constraints, domain distributions, and technical rigour of the Microsoft Certified: Fabric Analytics Engineer Associate exam.
          </p>
        </div>

        {/* 4 Stat Overview Tiles */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 shadow-lg text-center">
            <div className="text-2xl font-black text-white">{selectedQuestionCount}</div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mt-0.5">Questions</div>
          </div>
          <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 shadow-lg text-center">
            <div className="text-2xl font-black text-white">{selectedDuration}</div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mt-0.5">Minutes</div>
          </div>
          <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 shadow-lg text-center">
            <div className="text-2xl font-black text-emerald-400">70%</div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mt-0.5">To Pass (700)</div>
          </div>
          <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 shadow-lg text-center">
            <div className="text-2xl font-black text-amber-400">3</div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mt-0.5">Domains</div>
          </div>
        </div>

        {/* Configure Your Assessment Card */}
        <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl space-y-6">
          <h2 className="text-base font-bold text-white tracking-tight">Configure Your Assessment:</h2>

          {/* Number of Questions */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300">Number of Questions:</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {[20, 40, 50, questions.length].map((count) => (
                <button
                  key={count}
                  type="button"
                  onClick={() => setSelectedQuestionCount(count)}
                  className={`py-2.5 px-3 rounded-xl border text-xs font-bold transition-all ${
                    selectedQuestionCount === count
                      ? 'bg-amber-500/20 border-amber-500 text-amber-300 shadow-md shadow-amber-500/10'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
                  }`}
                >
                  {count === questions.length ? `All Qs (${count})` : `${count} Qs`}
                </button>
              ))}
            </div>
          </div>

          {/* Timer Duration */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300">Timer Duration:</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {[45, 90, 100, 120].map((mins) => (
                <button
                  key={mins}
                  type="button"
                  onClick={() => setSelectedDuration(mins)}
                  className={`py-2.5 px-3 rounded-xl border text-xs font-bold transition-all ${
                    selectedDuration === mins
                      ? 'bg-amber-500/20 border-amber-500 text-amber-300 shadow-md shadow-amber-500/10'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
                  }`}
                >
                  {mins} mins
                </button>
              ))}
            </div>
          </div>

          {/* Exam Starting Language */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <span>Exam Starting Language:</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setExamLanguage('FR')}
                className={`p-3.5 rounded-2xl border text-left transition-all flex items-center justify-between ${
                  examLanguage === 'FR'
                    ? 'bg-amber-500/15 border-amber-500/50 text-white ring-1 ring-amber-500/30'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🇫🇷</span>
                  <div>
                    <div className="text-sm font-bold text-white">Français</div>
                    <div className="text-xs text-slate-400">Traduction officielle française</div>
                  </div>
                </div>
                {examLanguage === 'FR' && (
                  <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                    Active
                  </span>
                )}
              </button>

              <button
                type="button"
                onClick={() => setExamLanguage('EN')}
                className={`p-3.5 rounded-2xl border text-left transition-all flex items-center justify-between ${
                  examLanguage === 'EN'
                    ? 'bg-amber-500/15 border-amber-500/50 text-white ring-1 ring-amber-500/30'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🇬🇧</span>
                  <div>
                    <div className="text-sm font-bold text-white">English</div>
                    <div className="text-xs text-slate-400">Original Pearson VUE English</div>
                  </div>
                </div>
                {examLanguage === 'EN' && (
                  <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                    Active
                  </span>
                )}
              </button>
            </div>
            <p className="text-[11px] text-slate-500 italic">
              The exam will load directly in this language. You can still switch anytime during the exam.
            </p>
          </div>

          {/* EXAM SKILLS DISTRIBUTION */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Exam Skills Distribution
            </div>
            <div className="space-y-1.5 text-xs text-slate-300">
              <div className="flex justify-between items-center py-1 border-b border-slate-900">
                <span className="text-slate-400"><strong className="text-amber-400 font-mono mr-2">01</strong>Plan, implement, and manage an analytics solution</span>
                <span className="font-semibold text-slate-400">10–15%</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-900">
                <span className="text-slate-400"><strong className="text-amber-400 font-mono mr-2">02</strong>Prepare and connect to data</span>
                <span className="font-semibold text-slate-400">40–45%</span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-slate-400"><strong className="text-amber-400 font-mono mr-2">03</strong>Model and explore data</span>
                <span className="font-semibold text-slate-400">40–45%</span>
              </div>
            </div>
          </div>

          {/* Exam Rules & Navigation Notice Box */}
          <div className="p-4 rounded-2xl bg-teal-500/5 border border-teal-500/20 space-y-2">
            <div className="flex items-center gap-2 text-teal-300 font-bold text-xs uppercase tracking-wider">
              <CheckCircle2 className="w-4 h-4 text-teal-400" />
              <span>Exam Rules & Navigation:</span>
            </div>
            <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
              <li>Explanations are strictly hidden during the exam to simulate real exam pressure.</li>
              <li>You can flag questions and navigate freely using the question grid.</li>
              <li>The timer counts down continuously and automatically submits when reaching 0:00.</li>
              <li>A full Fabric style diagnostic scorecard with weak area detection is revealed at the end.</li>
            </ul>
          </div>

          {/* Big Yellow CTA Button */}
          <button
            onClick={startAssessment}
            className="w-full py-4 rounded-2xl bg-gradient-to-r from-amber-400 via-amber-500 to-amber-600 hover:from-amber-300 hover:to-amber-500 text-slate-950 font-black text-base shadow-xl shadow-amber-500/25 transition-all transform active:scale-[0.99] flex items-center justify-center gap-2"
          >
            <span>Begin Assessment Now</span>
          </button>

        </div>
      </div>
    );
  }

  // 2. Active Exam Screen
  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-16 animate-fade-in text-white">
      
      {/* Pearson VUE Exam Header Bar */}
      <div className="bg-[#10172A] border border-slate-700/80 rounded-2xl p-4 sm:p-5 shadow-xl flex flex-wrap items-center justify-between gap-4">
        
        {/* Exam Title & Current Counter */}
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-teal-400 bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/20">
            Pearson VUE Simulation
          </span>
          <h1 className="text-base sm:text-lg font-bold text-white mt-1">
            DP-600: Implementing Analytics Solutions Using Microsoft Fabric
          </h1>
          <p className="text-xs text-slate-400">
            Question <span className="font-bold text-white">{currentIndex + 1}</span> of {examQuestions.length}
          </p>
        </div>

        {/* Center Timer */}
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl border font-mono text-sm font-bold shadow-inner ${
            timeLeftSeconds < 600
              ? 'bg-rose-500/20 border-rose-500/50 text-rose-300 animate-pulse'
              : 'bg-slate-900 border-slate-700 text-teal-300'
          }`}>
            <Clock className="w-4 h-4 text-teal-400" />
            <span>{formatTime(timeLeftSeconds)}</span>
          </div>

          <button
            onClick={() => setIsPaused(!isPaused)}
            className="text-xs px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-medium"
          >
            {isPaused ? 'Resume' : 'Pause'}
          </button>
        </div>

        {/* Action Controls (Flag, Case Study, MS Learn) */}
        <div className="flex items-center gap-2">
          {currentCaseStudy && (
            <button
              onClick={() => setShowCaseStudy(true)}
              className="px-3 py-1.5 rounded-xl bg-sky-500/20 hover:bg-sky-500/30 border border-sky-500/40 text-sky-300 text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              <Layers className="w-4 h-4" />
              Case Study
            </button>
          )}

          <button
            onClick={() => setShowMSLearn(true)}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition-all"
          >
            <BookOpen className="w-4 h-4 text-sky-400" />
            MS Learn
          </button>

          <button
            onClick={handleToggleFlag}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition-all ${
              isFlagged
                ? 'bg-amber-500/20 border-amber-500/50 text-amber-300'
                : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-400 hover:text-white'
            }`}
          >
            <Flag className={`w-4 h-4 ${isFlagged ? 'fill-amber-400 text-amber-400' : ''}`} />
            Flag for Review
          </button>
        </div>

      </div>

      {/* Main Question Body or Review Screen */}
      {!showReviewScreen ? (
        <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6">
          
          {/* Question Text & Code */}
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-800">
              <span className="font-semibold text-teal-400">{currentQuestion.topic}</span>
              <span>
                {isMulti ? (
                  <span className="text-teal-300 font-semibold flex items-center gap-1.5">
                    <CheckSquare className="w-3.5 h-3.5" />
                    Select {selectCount} answers ({getSelectedOptionsForCurrent().length} of {selectCount} chosen)
                  </span>
                ) : currentQuestion.type === 'drag_and_drop' ? (
                  <span className="text-teal-300 font-semibold">Sequence actions 1 to 4</span>
                ) : (
                  'Select the best answer.'
                )}
              </span>
            </div>

            <p className="text-base sm:text-lg font-medium text-slate-100 leading-relaxed">
              {currentQuestion.text}
            </p>

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

          {/* Options: Drag & Drop Ordering OR Multi-Select OR Multiple Choice */}
          {currentQuestion.type === 'drag_and_drop' ? (
            <StepOrderingQuestion
              question={currentQuestion}
              isAnswerRevealed={false}
              onAnswerSubmit={(orderedIds) => handleSelectOption(JSON.stringify(orderedIds))}
              savedAnswer={userAnswers[currentQuestion.id]}
            />
          ) : isMulti ? (
            <div className="space-y-3 pt-2">
              {currentQuestion.options.map((option) => {
                const currentList = getSelectedOptionsForCurrent();
                const isSelected = currentList.includes(option.id);

                return (
                  <button
                    key={option.id}
                    onClick={() => handleToggleMultiOption(option.id)}
                    className={`w-full text-left p-4 rounded-xl border flex items-start gap-3.5 transition-all text-sm leading-relaxed cursor-pointer ${
                      isSelected
                        ? 'bg-teal-500/15 border-teal-500 text-teal-100 shadow-md shadow-teal-500/10'
                        : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40 text-slate-300'
                    }`}
                  >
                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 border ${
                      isSelected
                        ? 'bg-teal-500 border-teal-400 text-white'
                        : 'bg-slate-800 border-slate-700 text-slate-400'
                    }`}>
                      {isSelected ? '✓' : option.id}
                    </div>
                    <div className="flex-1">{option.text}</div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="space-y-3 pt-2">
              {currentQuestion.options.map((option) => {
                const isSelected = userAnswers[currentQuestion.id] === option.id;

                return (
                  <button
                    key={option.id}
                    onClick={() => handleSelectOption(option.id)}
                    className={`w-full text-left p-4 rounded-xl border flex items-start gap-3.5 transition-all text-sm leading-relaxed cursor-pointer ${
                      isSelected
                        ? 'bg-teal-500/15 border-teal-500 text-teal-100 shadow-md shadow-teal-500/10'
                        : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40 text-slate-300'
                    }`}
                  >
                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 ${
                      isSelected
                        ? 'bg-teal-500 text-white'
                        : 'bg-slate-800 text-slate-400'
                    }`}>
                      {option.id}
                    </div>
                    <div className="flex-1">{option.text}</div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Navigation Controls */}
          <div className="flex items-center justify-between pt-6 border-t border-slate-800">
            <button
              onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
              disabled={currentIndex === 0}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-slate-800 text-xs font-semibold text-slate-200 flex items-center gap-1.5 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Previous
            </button>

            <button
              onClick={() => setShowReviewScreen(true)}
              className="px-4 py-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              Review All Questions ({examQuestions.length})
            </button>

            {currentIndex < examQuestions.length - 1 ? (
              <button
                onClick={() => setCurrentIndex(currentIndex + 1)}
                className="px-5 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 text-xs font-semibold text-white flex items-center gap-1.5 transition-colors"
              >
                Next
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={() => setShowReviewScreen(true)}
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-teal-500 to-sky-500 hover:from-teal-400 hover:to-sky-400 text-xs font-bold text-white flex items-center gap-1.5 transition-all shadow-md shadow-teal-500/20"
              >
                Finish & Review
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>

        </div>
      ) : (
        /* Pre-Submission Review Screen */
        <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <h2 className="text-xl font-bold text-white">Exam Review Screen</h2>
              <p className="text-xs text-slate-400">Verify all answers before final submission.</p>
            </div>
            <button
              onClick={() => setShowReviewScreen(false)}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200"
            >
              ← Back to Current Question
            </button>
          </div>

          {/* Warning if unanswered */}
          {totalUnanswered > 0 && (
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center gap-3 text-amber-200 text-xs">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
              <div>
                <span className="font-bold">You have {totalUnanswered} unanswered question(s).</span> In Microsoft certification exams, unanswered questions receive zero credit. There is no penalty for guessing!
              </div>
            </div>
          )}

          {/* Quick Metrics */}
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
              <div className="text-xl font-bold text-white">{totalAnswered} / {examQuestions.length}</div>
              <div className="text-[11px] text-slate-400">Answered</div>
            </div>
            <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
              <div className="text-xl font-bold text-amber-400">{totalUnanswered}</div>
              <div className="text-[11px] text-slate-400">Unanswered</div>
            </div>
            <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
              <div className="text-xl font-bold text-rose-400">{flaggedIds.length}</div>
              <div className="text-[11px] text-slate-400">Flagged for Review</div>
            </div>
          </div>

          {/* Question List Jump Grid */}
          <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {examQuestions.map((q, idx) => {
              const isAns = !!userAnswers[q.id];
              const isFlg = flaggedIds.includes(q.id);

              return (
                <div
                  key={q.id}
                  onClick={() => {
                    setCurrentIndex(idx);
                    setShowReviewScreen(false);
                  }}
                  className="bg-slate-900/70 hover:bg-slate-800/80 p-3 rounded-xl border border-slate-800 cursor-pointer flex items-center justify-between transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-md bg-slate-800 text-xs font-bold text-slate-300 flex items-center justify-center">
                      {idx + 1}
                    </span>
                    <span className="text-xs text-slate-200 line-clamp-1 max-w-lg">{q.text}</span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {isAns ? (
                      <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                        Answered ({userAnswers[q.id]})
                      </span>
                    ) : (
                      <span className="text-[10px] font-semibold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                        Unanswered
                      </span>
                    )}

                    {isFlg && (
                      <span className="text-[10px] font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20 flex items-center gap-1">
                        <Flag className="w-3 h-3 fill-rose-400" />
                        Flagged
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Final Submit Button */}
          <div className="pt-4 border-t border-slate-800 flex justify-end">
            <button
              onClick={handleSubmitExam}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-sky-500 hover:from-teal-400 hover:to-sky-400 text-white font-bold text-sm shadow-xl shadow-teal-500/20 flex items-center gap-2 transition-all active:scale-95"
            >
              <CheckCircle2 className="w-5 h-5" />
              Submit Exam & Generate Official Scorecard
            </button>
          </div>

        </div>
      )}

      {/* Pearson VUE Question Navigator Matrix Grid */}
      <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
        <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-800">
          <span className="font-semibold text-slate-300">Question Matrix Navigation</span>
          <div className="flex items-center gap-4 text-[11px]">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-teal-500 ring-2 ring-teal-300"></span> Current
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-teal-900 border border-teal-600"></span> Answered
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-slate-800 border border-slate-700"></span> Unanswered
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-amber-500"></span> Flagged
            </span>
          </div>
        </div>

        <div className="grid grid-cols-10 sm:grid-cols-20 gap-1.5 pt-1">
          {examQuestions.map((q, idx) => {
            const isCurrent = idx === currentIndex;
            const isAns = !!userAnswers[q.id];
            const isFlg = flaggedIds.includes(q.id);

            let btnStyle = 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-600';

            if (isCurrent) {
              btnStyle = 'bg-teal-500 text-white font-extrabold ring-2 ring-teal-300 shadow-md shadow-teal-500/30';
            } else if (isFlg) {
              btnStyle = 'bg-amber-500/20 border-amber-500 text-amber-300 font-bold';
            } else if (isAns) {
              btnStyle = 'bg-teal-900/60 border-teal-700/80 text-teal-300 font-semibold';
            }

            return (
              <button
                key={q.id}
                onClick={() => {
                  setCurrentIndex(idx);
                  setShowReviewScreen(false);
                }}
                className={`h-8 rounded-lg border text-xs flex items-center justify-center relative transition-all ${btnStyle}`}
              >
                {idx + 1}
                {isFlg && !isCurrent && (
                  <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-amber-400"></span>
                )}
              </button>
            );
          })}
        </div>
      </div>

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
