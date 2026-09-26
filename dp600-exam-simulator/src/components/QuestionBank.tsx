import React, { useState, useMemo } from 'react';
import { Question, DomainId, DOMAINS, UserStats } from '../types';
import { storageService } from '../services/storageService';
import { 
  Search, 
  Filter, 
  Star, 
  ArrowRight, 
  CheckCircle2, 
  XCircle, 
  Code2, 
  BookOpen, 
  Play, 
  ChevronDown, 
  ChevronUp,
  Layers,
  Sparkles,
  ListOrdered,
  CheckSquare
} from 'lucide-react';

interface QuestionBankProps {
  questions: Question[];
  stats: UserStats;
  onPracticeQuestion: (questionId: string) => void;
  onPracticeAll: () => void;
  onStatsChange: () => void;
}

export const QuestionBank: React.FC<QuestionBankProps> = ({
  questions,
  stats,
  onPracticeQuestion,
  onPracticeAll,
  onStatsChange
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDomain, setSelectedDomain] = useState<DomainId | 'all'>('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'unanswered' | 'incorrect' | 'bookmarked'>('all');
  const [selectedType, setSelectedType] = useState<'all' | 'multiple_choice' | 'multi_select' | 'drag_and_drop'>('all');
  const [expandedQuestionIds, setExpandedQuestionIds] = useState<string[]>([]);

  const toggleExpand = (qId: string) => {
    setExpandedQuestionIds(prev => 
      prev.includes(qId) ? prev.filter(id => id !== qId) : [...prev, qId]
    );
  };

  const handleToggleBookmark = (qId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    storageService.toggleBookmark(qId);
    onStatsChange();
  };

  // Filter questions
  const filteredQuestions = useMemo(() => {
    return questions.filter(q => {
      // Domain filter
      if (selectedDomain !== 'all' && q.domain !== selectedDomain) return false;

      // Difficulty filter
      if (selectedDifficulty !== 'all' && q.difficulty !== selectedDifficulty) return false;

      // Question Type filter
      if (selectedType !== 'all') {
        const qType = q.type || 'multiple_choice';
        if (qType !== selectedType) return false;
      }

      // Status filter
      const attempt = stats.answeredQuestionIds[q.id];
      const isBookmarked = stats.bookmarkedQuestionIds.includes(q.id);

      if (selectedStatus === 'unanswered' && attempt) return false;
      if (selectedStatus === 'incorrect' && (!attempt || attempt.isCorrect)) return false;
      if (selectedStatus === 'bookmarked' && !isBookmarked) return false;

      // Search query
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase().trim();
        const inId = q.id.toLowerCase().includes(query);
        const inText = q.text.toLowerCase().includes(query);
        const inTopic = q.topic.toLowerCase().includes(query);
        const inDomain = DOMAINS[q.domain].name.toLowerCase().includes(query);
        const inExplanation = q.explanation.toLowerCase().includes(query);
        const inOptions = q.options.some(opt => opt.text.toLowerCase().includes(query));
        const inCode = q.codeSnippet?.code.toLowerCase().includes(query);

        if (!inId && !inText && !inTopic && !inDomain && !inExplanation && !inOptions && !inCode) {
          return false;
        }
      }

      return true;
    });
  }, [questions, searchQuery, selectedDomain, selectedDifficulty, selectedStatus, selectedType, stats]);

  // Domain Counts
  const d1Count = questions.filter(q => q.domain === 'domain1').length;
  const d2Count = questions.filter(q => q.domain === 'domain2').length;
  const d3Count = questions.filter(q => q.domain === 'domain3').length;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-20 animate-fade-in text-white">
      
      {/* Top Banner */}
      <div className="bg-gradient-to-br from-slate-900 via-[#0B1528] to-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-300 text-xs font-semibold">
              <BookOpen className="w-3.5 h-3.5" />
              <span>VERIFIED QUESTION DIRECTORY</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Comprehensive <span className="bg-gradient-to-r from-teal-400 via-sky-400 to-blue-400 bg-clip-text text-transparent">Question Bank</span>
            </h1>
            <p className="text-sm text-slate-300">
              Browse, filter, and inspect all {questions.length} verified DP-600 practice questions with real exam distractors, deep rationales, and official Microsoft Learn citations.
            </p>
          </div>

          <button
            onClick={onPracticeAll}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-extrabold text-xs sm:text-sm flex items-center gap-2 shadow-lg shadow-amber-500/20 active:scale-95 transition-all shrink-0 cursor-pointer self-start sm:self-center"
          >
            <Play className="w-4 h-4 fill-slate-950" />
            <span>Practice All ({questions.length})</span>
          </button>
        </div>
      </div>

      {/* Search & Filter Controls */}
      <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-lg space-y-4">
        
        {/* Search Input Bar */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search questions by keyword, DAX function, PySpark method, tag or ID..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-teal-400 focus:ring-1 focus:ring-teal-400 transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-white"
            >
              Clear
            </button>
          )}
        </div>

        {/* Dropdown Filters Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          
          {/* Domain Filter */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Domain</label>
            <select
              value={selectedDomain}
              onChange={(e) => setSelectedDomain(e.target.value as any)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-teal-400"
            >
              <option value="all">All Domains ({questions.length})</option>
              <option value="domain1">Domain 1: Plan & Manage ({d1Count})</option>
              <option value="domain2">Domain 2: Prepare & Connect ({d2Count})</option>
              <option value="domain3">Domain 3: Model & Explore ({d3Count})</option>
            </select>
          </div>

          {/* Difficulty Filter */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Difficulty</label>
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-teal-400"
            >
              <option value="all">All Difficulties</option>
              <option value="Easy">Easy</option>
              <option value="Medium">Medium</option>
              <option value="Hard">Hard</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Study Status</label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value as any)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-teal-400"
            >
              <option value="all">All Questions</option>
              <option value="unanswered">Unanswered Only</option>
              <option value="incorrect">Incorrect Only</option>
              <option value="bookmarked">Bookmarked Only</option>
            </select>
          </div>

          {/* Question Type Filter */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Question Type</label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as any)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-teal-400"
            >
              <option value="all">All Types</option>
              <option value="multiple_choice">Single Choice</option>
              <option value="multi_select">Multi-Select Checkboxes</option>
              <option value="drag_and_drop">Drag & Drop Ordering</option>
            </select>
          </div>

        </div>
      </div>

      {/* Showing Count */}
      <div className="flex items-center justify-between text-xs text-slate-400 px-1">
        <span>
          Showing <span className="font-bold text-white">{filteredQuestions.length}</span> of {questions.length} questions
        </span>
        {(searchQuery || selectedDomain !== 'all' || selectedDifficulty !== 'all' || selectedStatus !== 'all' || selectedType !== 'all') && (
          <button
            onClick={() => {
              setSearchQuery('');
              setSelectedDomain('all');
              setSelectedDifficulty('all');
              setSelectedStatus('all');
              setSelectedType('all');
            }}
            className="text-teal-400 hover:text-teal-300 font-medium"
          >
            Reset All Filters
          </button>
        )}
      </div>

      {/* Question Cards List */}
      {filteredQuestions.length === 0 ? (
        <div className="bg-[#10172A] border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
          <BookOpen className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-base font-semibold text-slate-200">No questions match your current search and filters.</p>
          <p className="text-xs text-slate-500 mt-1">Try resetting your search query or clearing your filter pills.</p>
        </div>
      ) : (
        <div className="space-y-3.5">
          {filteredQuestions.map((q) => {
            const isBookmarked = stats.bookmarkedQuestionIds.includes(q.id);
            const attempt = stats.answeredQuestionIds[q.id];
            const isExpanded = expandedQuestionIds.includes(q.id);
            const isOrdering = q.type === 'drag_and_drop';
            const isMulti = q.type === 'multi_select' || (q.correctOptionIds && q.correctOptionIds.length > 1);

            return (
              <div
                key={q.id}
                className="bg-[#10172A]/90 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 sm:p-6 shadow-md transition-all hover:bg-[#121B30]"
              >
                {/* Meta Bar */}
                <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
                  <div className="flex flex-wrap items-center gap-2">
                    {/* ID Pill */}
                    <span className="font-mono text-[11px] font-bold px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      {q.id.toUpperCase()}
                    </span>

                    {/* Domain Pill */}
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-teal-500/10 text-teal-300 border border-teal-500/20">
                      {DOMAINS[q.domain].code}
                    </span>

                    {/* Difficulty */}
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      q.difficulty === 'Hard' ? 'bg-rose-500/10 text-rose-300' :
                      q.difficulty === 'Medium' ? 'bg-amber-500/10 text-amber-300' :
                      'bg-emerald-500/10 text-emerald-300'
                    }`}>
                      {q.difficulty.toUpperCase()}
                    </span>

                    {/* Type Badge */}
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 flex items-center gap-1">
                      {isOrdering ? (
                        <>
                          <ListOrdered className="w-3 h-3 text-teal-400" />
                          <span>ORDERING</span>
                        </>
                      ) : isMulti ? (
                        <>
                          <CheckSquare className="w-3 h-3 text-sky-400" />
                          <span>MULTI-SELECT</span>
                        </>
                      ) : (
                        <span>SINGLE</span>
                      )}
                    </span>

                    {/* Attempt Status Badge */}
                    {attempt && (
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1 ${
                        attempt.isCorrect 
                          ? 'bg-emerald-500/10 text-emerald-400' 
                          : 'bg-rose-500/10 text-rose-400'
                      }`}>
                        {attempt.isCorrect ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                        {attempt.isCorrect ? 'PASSED' : 'INCORRECT'}
                      </span>
                    )}
                  </div>

                  {/* Actions: Bookmark & Practice */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => handleToggleBookmark(q.id, e)}
                      className={`p-1.5 rounded-lg border transition-colors cursor-pointer ${
                        isBookmarked 
                          ? 'bg-amber-500/20 border-amber-500/40 text-amber-400' 
                          : 'bg-slate-800/80 border-slate-700 text-slate-400 hover:text-white'
                      }`}
                      title={isBookmarked ? 'Remove bookmark' : 'Bookmark this question'}
                    >
                      <Star className={`w-3.5 h-3.5 ${isBookmarked ? 'fill-amber-400 text-amber-400' : ''}`} />
                    </button>

                    <button
                      onClick={() => onPracticeQuestion(q.id)}
                      className="px-3 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs flex items-center gap-1 transition-all active:scale-95 cursor-pointer"
                    >
                      <span>Practice</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Question Stem */}
                <div className="pt-3 space-y-3">
                  <p className="text-xs sm:text-sm font-medium text-slate-100 leading-relaxed">
                    {q.text}
                  </p>

                  {/* Code Snippet if present */}
                  {q.codeSnippet && (
                    <div className="rounded-lg overflow-hidden border border-slate-800 bg-[#090D16] text-xs font-mono p-3 text-teal-200">
                      <code>{q.codeSnippet.code}</code>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                    <span className="text-[11px] text-slate-400">
                      Topic: <span className="text-slate-300 font-semibold">{q.topic}</span> • {DOMAINS[q.domain].name}
                    </span>

                    <button
                      onClick={() => toggleExpand(q.id)}
                      className="text-xs text-teal-400 hover:text-teal-300 font-semibold flex items-center gap-1 cursor-pointer"
                    >
                      <span>{isExpanded ? 'Hide Solution' : 'View Solution'}</span>
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Collapsible Answer & Explanation Preview */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-slate-800 space-y-3 animate-fade-in bg-slate-950/40 p-4 rounded-xl">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span className="text-xs font-bold text-white">
                        {isOrdering ? (
                          <span>Correct Sequence: 1 to {q.orderingSteps?.length || 4}</span>
                        ) : isMulti ? (
                          <span>Correct Keys: {(q.correctOptionIds || [q.correctOptionId]).join(', ')}</span>
                        ) : (
                          <span>Correct Option: {q.correctOptionId}</span>
                        )}
                      </span>
                    </div>

                    {/* Options list */}
                    <div className="grid grid-cols-1 gap-2 pt-1">
                      {isOrdering ? (
                        q.orderingSteps?.map((s, idx) => (
                          <div key={s.id} className="text-xs p-2.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center gap-2 text-slate-300">
                            <span className="w-5 h-5 rounded bg-teal-500 text-white font-bold flex items-center justify-center text-[10px]">
                              {idx + 1}
                            </span>
                            <span>{s.text}</span>
                          </div>
                        ))
                      ) : (
                        q.options.map((opt) => {
                          const isCorrect = isMulti 
                            ? (q.correctOptionIds || []).includes(opt.id)
                            : opt.id === q.correctOptionId;

                          return (
                            <div 
                              key={opt.id} 
                              className={`text-xs p-2.5 rounded-lg border flex items-start gap-2.5 ${
                                isCorrect 
                                  ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-200 font-medium' 
                                  : 'bg-slate-900/60 border-slate-800/80 text-slate-400'
                              }`}
                            >
                              <span className={`w-5 h-5 rounded flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5 ${
                                isCorrect ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-400'
                              }`}>
                                {opt.id}
                              </span>
                              <span className="flex-1">{opt.text}</span>
                              {isCorrect && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
                            </div>
                          );
                        })
                      )}
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed pt-2 border-t border-slate-800/80">
                      <span className="font-bold text-teal-300">Explanation: </span>
                      {q.explanation}
                    </p>

                    {q.msLearnUrl && (
                      <div className="pt-1">
                        <a
                          href={q.msLearnUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-sky-400 hover:text-sky-300 font-semibold inline-flex items-center gap-1"
                        >
                          <span>{q.msLearnTitle || 'Read on Microsoft Learn'}</span>
                          <ArrowRight className="w-3 h-3" />
                        </a>
                      </div>
                    )}
                  </div>
                )}

              </div>
            );
          })}
        </div>
      )}

    </div>
  );
};
