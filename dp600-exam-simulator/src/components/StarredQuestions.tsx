import React from 'react';
import { Question, UserStats, DOMAINS } from '../types';
import { storageService } from '../services/storageService';
import { 
  Star, 
  BookOpen, 
  ArrowRight, 
  Trash2, 
  Sparkles, 
  CheckCircle2,
  Code2
} from 'lucide-react';

interface StarredQuestionsProps {
  questions: Question[];
  stats: UserStats;
  onPracticeQuestion: (questionId: string) => void;
  onPracticeAllStarred: (questionIds: string[]) => void;
  onStatsChange: () => void;
}

export const StarredQuestions: React.FC<StarredQuestionsProps> = ({
  questions,
  stats,
  onPracticeQuestion,
  onPracticeAllStarred,
  onStatsChange
}) => {
  const starredList = questions.filter(q => stats.bookmarkedQuestionIds.includes(q.id));

  const handleUnstar = (qId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    storageService.toggleBookmark(qId);
    onStatsChange();
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-20 animate-fade-in text-white">
      
      {/* Header Banner */}
      <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <Star className="w-6 h-6 text-amber-400 fill-amber-400" />
            <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight">
              Starred & Saved Questions
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-300">
            Quickly revisit and drill the key Fabric questions you've saved for targeted revision.
          </p>
        </div>

        {starredList.length > 0 && (
          <button
            onClick={() => onPracticeAllStarred(starredList.map(q => q.id))}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs sm:text-sm shadow-lg shadow-amber-500/20 transition-all active:scale-95 shrink-0"
          >
            <span>Practice All Starred ({starredList.length})</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Starred Questions List */}
      {starredList.length === 0 ? (
        <div className="bg-[#10172A] border border-slate-800 rounded-3xl p-12 text-center space-y-4 shadow-xl">
          <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto text-amber-400">
            <Star className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-white">No Starred Questions Yet</h3>
            <p className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto">
              When reviewing questions in Practice Mode, Mock Exams, or the Question Bank, tap the Star icon to bookmark questions here for quick drill sessions.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {starredList.map((q) => {
            const domainName = DOMAINS[q.domain]?.name || q.domain;

            return (
              <div
                key={q.id}
                onClick={() => onPracticeQuestion(q.id)}
                className="bg-[#10172A] border border-slate-800 hover:border-slate-700/80 rounded-2xl p-5 shadow-lg space-y-3 transition-all cursor-pointer group"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                      {q.id}
                    </span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-300 border border-teal-500/20">
                      {domainName}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      q.difficulty === 'Easy' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                      q.difficulty === 'Medium' ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20' :
                      'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                    }`}>
                      {q.difficulty?.toUpperCase()}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => handleUnstar(q.id, e)}
                      className="p-1.5 rounded-lg bg-amber-500/10 hover:bg-rose-500/20 text-amber-400 hover:text-rose-400 border border-amber-500/20 hover:border-rose-500/30 transition-colors"
                      title="Remove from starred"
                    >
                      <Star className="w-4 h-4 fill-amber-400 hover:fill-transparent" />
                    </button>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onPracticeQuestion(q.id);
                      }}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-teal-300 border border-slate-800 transition-colors"
                    >
                      <span>Practice</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <p className="text-sm font-semibold text-slate-100 leading-relaxed group-hover:text-teal-200 transition-colors">
                  {q.text}
                </p>

                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                  <span>Topic: {q.topic}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
};
export default StarredQuestions;
