import React, { useState, useRef, useEffect } from 'react';
import { UserStats } from '../types';
import { 
  Flame, 
  Award, 
  BookOpen, 
  CheckCircle2, 
  FileText, 
  UploadCloud, 
  PlayCircle,
  Database,
  ChevronDown,
  Calendar,
  HelpCircle,
  BarChart3,
  Sparkles,
  Layers,
  Bookmark,
  TrendingUp,
  Star,
  Settings
} from 'lucide-react';

export type ActiveTab = 
  | 'dashboard' 
  | 'practice' 
  | 'mock-exam' 
  | 'mistake-review'
  | 'study-guides' 
  | '7-day-plan' 
  | 'question-bank' 
  | 'analytics'
  | 'starred'
  | 'settings'
  | 'importer' 
  | 'results';

interface NavbarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  stats: UserStats;
  totalQuestions: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  stats,
  totalQuestions
}) => {
  const [studyMenuOpen, setStudyMenuOpen] = useState(false);
  const [practiceMenuOpen, setPracticeMenuOpen] = useState(false);
  const [toolsMenuOpen, setToolsMenuOpen] = useState(false);
  const [lang, setLang] = useState<'EN' | 'FR'>('EN');

  const studyRef = useRef<HTMLDivElement>(null);
  const practiceRef = useRef<HTMLDivElement>(null);
  const toolsRef = useRef<HTMLDivElement>(null);

  const accuracy = stats.totalAnswered > 0 
    ? Math.round((stats.correctAnswers / stats.totalAnswered) * 100) 
    : 0;

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (studyRef.current && !studyRef.current.contains(event.target as Node)) {
        setStudyMenuOpen(false);
      }
      if (practiceRef.current && !practiceRef.current.contains(event.target as Node)) {
        setPracticeMenuOpen(false);
      }
      if (toolsRef.current && !toolsRef.current.contains(event.target as Node)) {
        setToolsMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isStudyActive = activeTab === 'study-guides' || activeTab === '7-day-plan' || activeTab === 'question-bank';
  const isPracticeActive = activeTab === 'practice' || activeTab === 'mock-exam' || activeTab === 'mistake-review';
  const isToolsActive = activeTab === 'analytics' || activeTab === 'starred' || activeTab === 'settings' || activeTab === 'importer' || activeTab === 'results';

  return (
    <header className="sticky top-0 z-50 bg-[#0B101D]/95 backdrop-blur-md border-b border-slate-800 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Certification Title */}
          <div 
            onClick={() => {
              setActiveTab('dashboard');
              setStudyMenuOpen(false);
              setPracticeMenuOpen(false);
              setToolsMenuOpen(false);
            }}
            className="flex items-center gap-3 cursor-pointer group shrink-0"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#0078D4] to-[#00A389] p-0.5 shadow-lg shadow-teal-500/10 group-hover:scale-105 transition-transform">
              <div className="w-full h-full bg-[#0B101D] rounded-[10px] flex items-center justify-center">
                <Database className="w-5 h-5 text-teal-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-base tracking-tight bg-gradient-to-r from-teal-400 via-sky-400 to-blue-400 bg-clip-text text-transparent">
                  DP-600
                </span>
                <span className="text-[10px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  PRO
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">Fabric Analytics Engineer Exam Simulator</p>
            </div>
          </div>

          {/* Center Navigation Links & Dropdowns */}
          <nav className="hidden md:flex items-center gap-1.5">
            {/* 1. Dashboard */}
            <button
              onClick={() => {
                setActiveTab('dashboard');
                setStudyMenuOpen(false);
                setPracticeMenuOpen(false);
                setToolsMenuOpen(false);
              }}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'dashboard'
                  ? 'bg-teal-500/10 text-teal-400 border border-teal-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <BarChart3 className="w-4 h-4 text-slate-400" />
              <span>Dashboard</span>
            </button>

            {/* 2. Study & Concepts Dropdown (Matches reference screenshot 1, 2, 3) */}
            <div className="relative" ref={studyRef}>
              <button
                onClick={() => {
                  setStudyMenuOpen(prev => !prev);
                  setPracticeMenuOpen(false);
                  setToolsMenuOpen(false);
                }}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  isStudyActive
                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/40 shadow-sm'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <BookOpen className="w-4 h-4 text-amber-400" />
                <span>Study & Concepts</span>
                <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${studyMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {studyMenuOpen && (
                <div className="absolute top-full left-0 mt-2 w-80 bg-[#10172A] border border-slate-700/80 rounded-2xl shadow-2xl p-2 space-y-1 z-50 animate-fade-in backdrop-blur-xl">
                  {/* Option 1: Study Guide */}
                  <button
                    onClick={() => {
                      setActiveTab('study-guides');
                      setStudyMenuOpen(false);
                    }}
                    className={`w-full text-left p-2.5 rounded-xl transition-all flex items-start gap-3 ${
                      activeTab === 'study-guides'
                        ? 'bg-amber-500/20 border border-amber-500/40 text-amber-200'
                        : 'hover:bg-slate-800/80 text-slate-200'
                    }`}
                  >
                    <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0 mt-0.5">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">Study Guide</div>
                      <div className="text-xs text-slate-400">Core concepts, Fabric architecture & exam traps</div>
                    </div>
                  </button>

                  {/* Option 2: 7-Day Plan */}
                  <button
                    onClick={() => {
                      setActiveTab('7-day-plan');
                      setStudyMenuOpen(false);
                    }}
                    className={`w-full text-left p-2.5 rounded-xl transition-all flex items-start gap-3 ${
                      activeTab === '7-day-plan'
                        ? 'bg-amber-500/20 border border-amber-500/40 text-amber-200'
                        : 'hover:bg-slate-800/80 text-slate-200'
                    }`}
                  >
                    <div className="p-2 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20 shrink-0 mt-0.5">
                      <Calendar className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">7-Day Plan</div>
                      <div className="text-xs text-slate-400">Structured day-by-day roadmap</div>
                    </div>
                  </button>

                  {/* Option 3: Question Bank */}
                  <button
                    onClick={() => {
                      setActiveTab('question-bank');
                      setStudyMenuOpen(false);
                    }}
                    className={`w-full text-left p-2.5 rounded-xl transition-all flex items-start gap-3 ${
                      activeTab === 'question-bank'
                        ? 'bg-amber-500/20 border border-amber-500/40 text-amber-200'
                        : 'hover:bg-slate-800/80 text-slate-200'
                    }`}
                  >
                    <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20 shrink-0 mt-0.5">
                      <HelpCircle className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">Question Bank</div>
                      <div className="text-xs text-slate-400">{totalQuestions} verified practice questions</div>
                    </div>
                  </button>
                </div>
              )}
            </div>

            {/* 3. Practice & Exam Dropdown (Matches Reference Screenshot 1) */}
            <div className="relative" ref={practiceRef}>
              <button
                onClick={() => {
                  setPracticeMenuOpen(prev => !prev);
                  setStudyMenuOpen(false);
                  setToolsMenuOpen(false);
                }}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  isPracticeActive
                    ? 'bg-teal-500/10 text-teal-400 border border-teal-500/40'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <CheckCircle2 className="w-4 h-4 text-teal-400" />
                <span>Practice & Exam</span>
                <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${practiceMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {practiceMenuOpen && (
                <div className="absolute top-full left-0 mt-2 w-72 bg-[#10172A] border border-slate-700/80 rounded-2xl shadow-2xl p-2 space-y-1 z-50 animate-fade-in backdrop-blur-xl">
                  {/* Option 1: Practice */}
                  <button
                    onClick={() => {
                      setActiveTab('practice');
                      setPracticeMenuOpen(false);
                    }}
                    className={`w-full text-left p-2.5 rounded-xl transition-all flex items-start gap-3 ${
                      activeTab === 'practice'
                        ? 'bg-teal-500/20 border border-teal-500/40 text-teal-200'
                        : 'hover:bg-slate-800/80 text-slate-200'
                    }`}
                  >
                    <div className="p-2 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20 shrink-0 mt-0.5">
                      <BookOpen className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">Practice</div>
                      <div className="text-xs text-slate-400">Instant step-by-step feedback</div>
                    </div>
                  </button>

                  {/* Option 2: Mock Exam */}
                  <button
                    onClick={() => {
                      setActiveTab('mock-exam');
                      setPracticeMenuOpen(false);
                    }}
                    className={`w-full text-left p-2.5 rounded-xl transition-all flex items-start gap-3 ${
                      activeTab === 'mock-exam'
                        ? 'bg-amber-500/20 border border-amber-500/40 text-amber-200'
                        : 'hover:bg-slate-800/80 text-slate-200'
                    }`}
                  >
                    <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 shrink-0 mt-0.5">
                      <PlayCircle className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">Mock Exam</div>
                      <div className="text-xs text-slate-400">Official timed exam simulation</div>
                    </div>
                  </button>

                  {/* Option 3: Review (Mistake Review) */}
                  <button
                    onClick={() => {
                      setActiveTab('mistake-review');
                      setPracticeMenuOpen(false);
                    }}
                    className={`w-full text-left p-2.5 rounded-xl transition-all flex items-start gap-3 ${
                      activeTab === 'mistake-review'
                        ? 'bg-rose-500/20 border border-rose-500/40 text-rose-200'
                        : 'hover:bg-slate-800/80 text-slate-200'
                    }`}
                  >
                    <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20 shrink-0 mt-0.5">
                      <Bookmark className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">Review</div>
                      <div className="text-xs text-slate-400">Drill and fix your missed questions</div>
                    </div>
                  </button>
                </div>
              )}
            </div>

            {/* 4. Analytics & Tools Dropdown (Matches Reference Screenshot 1 & 2) */}
            <div className="relative" ref={toolsRef}>
              <button
                onClick={() => {
                  setToolsMenuOpen(prev => !prev);
                  setStudyMenuOpen(false);
                  setPracticeMenuOpen(false);
                }}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  isToolsActive
                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/40'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <TrendingUp className="w-4 h-4 text-amber-400" />
                <span>Analytics & Tools</span>
                <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${toolsMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {toolsMenuOpen && (
                <div className="absolute top-full left-0 mt-2 w-72 bg-[#10172A] border border-slate-700/80 rounded-2xl shadow-2xl p-2 space-y-1 z-50 animate-fade-in backdrop-blur-xl">
                  {/* Option 1: Analytics */}
                  <button
                    onClick={() => {
                      setActiveTab('analytics');
                      setToolsMenuOpen(false);
                    }}
                    className={`w-full text-left p-2.5 rounded-xl transition-all flex items-start gap-3 ${
                      activeTab === 'analytics'
                        ? 'bg-amber-500/20 border border-amber-500/40 text-amber-200'
                        : 'hover:bg-slate-800/80 text-slate-200'
                    }`}
                  >
                    <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0 mt-0.5">
                      <TrendingUp className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">Analytics</div>
                      <div className="text-xs text-slate-400">Skills radar and diagnostic telemetry</div>
                    </div>
                  </button>

                  {/* Option 2: Starred */}
                  <button
                    onClick={() => {
                      setActiveTab('starred');
                      setToolsMenuOpen(false);
                    }}
                    className={`w-full text-left p-2.5 rounded-xl transition-all flex items-start gap-3 ${
                      activeTab === 'starred'
                        ? 'bg-amber-500/20 border border-amber-500/40 text-amber-200'
                        : 'hover:bg-slate-800/80 text-slate-200'
                    }`}
                  >
                    <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0 mt-0.5">
                      <Star className="w-4 h-4 fill-amber-400" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">Starred</div>
                      <div className="text-xs text-slate-400">Your starred and saved questions</div>
                    </div>
                  </button>

                  {/* Option 3: Settings */}
                  <button
                    onClick={() => {
                      setActiveTab('settings');
                      setToolsMenuOpen(false);
                    }}
                    className={`w-full text-left p-2.5 rounded-xl transition-all flex items-start gap-3 ${
                      activeTab === 'settings'
                        ? 'bg-amber-500/20 border border-amber-500/40 text-amber-200'
                        : 'hover:bg-slate-800/80 text-slate-200'
                    }`}
                  >
                    <div className="p-2 rounded-xl bg-slate-800 text-slate-300 border border-slate-700 shrink-0 mt-0.5">
                      <Settings className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">Settings</div>
                      <div className="text-xs text-slate-400">Theme mode, backup and reset</div>
                    </div>
                  </button>

                  {/* Option 4: Import Questions */}
                  <button
                    onClick={() => {
                      setActiveTab('importer');
                      setToolsMenuOpen(false);
                    }}
                    className={`w-full text-left p-2.5 rounded-xl transition-all flex items-start gap-3 ${
                      activeTab === 'importer'
                        ? 'bg-purple-500/20 border border-purple-500/40 text-purple-200'
                        : 'hover:bg-slate-800/80 text-slate-200'
                    }`}
                  >
                    <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 shrink-0 mt-0.5">
                      <UploadCloud className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">Import Questions</div>
                      <div className="text-xs text-slate-400">Parse MS Learn exams or JSON</div>
                    </div>
                  </button>
                </div>
              )}
            </div>

          </nav>

          {/* Right Metrics & Quick Exam CTA */}
          <div className="flex items-center gap-3">
            {/* Language Toggle */}
            <div className="hidden lg:flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs font-semibold text-slate-400">
              <button 
                onClick={() => setLang('FR')}
                className={`px-2 py-1 rounded transition-colors ${lang === 'FR' ? 'bg-slate-800 text-white font-bold' : 'hover:text-slate-200'}`}
              >
                🇫🇷 FR
              </button>
              <button 
                onClick={() => setLang('EN')}
                className={`px-2 py-1 rounded transition-colors ${lang === 'EN' ? 'bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30' : 'hover:text-slate-200'}`}
              >
                🇬🇧 EN
              </button>
            </div>

            {/* Streak Counter */}
            <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-orange-500/10 border border-orange-500/20 text-orange-400 text-xs font-semibold" title="Daily Study Streak">
              <Flame className="w-4 h-4 text-orange-400 animate-pulse" />
              <span>{stats.streakDays}d</span>
            </div>

            {/* Overall Accuracy Pill */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300" title="Overall Accuracy">
              <span className="w-2 h-2 rounded-full bg-teal-400"></span>
              <span className="font-semibold text-white">{accuracy}%</span>
              <span className="text-slate-500">acc</span>
            </div>

            {/* Start Mock Exam CTA */}
            <button
              onClick={() => {
                setActiveTab('mock-exam');
                setStudyMenuOpen(false);
                setPracticeMenuOpen(false);
                setToolsMenuOpen(false);
              }}
              className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 text-xs sm:text-sm font-bold shadow-md shadow-amber-500/20 transition-all flex items-center gap-1.5 active:scale-95"
            >
              <Award className="w-4 h-4 text-slate-950" />
              <span>Start Exam</span>
            </button>
          </div>

        </div>
      </div>

      {/* Mobile navigation row for smaller screens */}
      <div className="md:hidden flex items-center justify-around py-2 border-t border-slate-800/80 bg-[#090D17] text-xs">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-2 py-1 rounded ${activeTab === 'dashboard' ? 'text-teal-400 font-bold' : 'text-slate-400'}`}
        >
          Dashboard
        </button>
        <button
          onClick={() => setActiveTab('7-day-plan')}
          className={`px-2 py-1 rounded ${activeTab === '7-day-plan' ? 'text-amber-400 font-bold' : 'text-slate-400'}`}
        >
          7-Day Plan
        </button>
        <button
          onClick={() => setActiveTab('question-bank')}
          className={`px-2 py-1 rounded ${activeTab === 'question-bank' ? 'text-sky-400 font-bold' : 'text-slate-400'}`}
        >
          Questions
        </button>
        <button
          onClick={() => setActiveTab('study-guides')}
          className={`px-2 py-1 rounded ${activeTab === 'study-guides' ? 'text-teal-400 font-bold' : 'text-slate-400'}`}
        >
          Guides
        </button>
        <button
          onClick={() => setActiveTab('practice')}
          className={`px-2 py-1 rounded ${activeTab === 'practice' ? 'text-emerald-400 font-bold' : 'text-slate-400'}`}
        >
          Practice
        </button>
      </div>
    </header>
  );
};
