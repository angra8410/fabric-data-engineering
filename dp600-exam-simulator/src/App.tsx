import React, { useState } from 'react';
import { storageService } from './services/storageService';
import { Question, UserStats, ExamAttempt, DomainId, ExamId, EXAMS } from './types';
import { Navbar, ActiveTab } from './components/Navbar';
import { Dashboard } from './components/Dashboard';
import { PracticeMode } from './components/PracticeMode';
import { MockExam } from './components/MockExam';
import { ExamResults } from './components/ExamResults';
import { StudyGuides } from './components/StudyGuides';
import { SevenDayPlan } from './components/SevenDayPlan';
import { QuestionBank } from './components/QuestionBank';
import { MistakeReview } from './components/MistakeReview';
import { PerformanceAnalytics } from './components/PerformanceAnalytics';
import { StarredQuestions } from './components/StarredQuestions';
import { SettingsPage } from './components/SettingsPage';
import { QuestionImporter } from './components/QuestionImporter';

export const App: React.FC = () => {
  const [activeExam, setActiveExam] = useState<ExamId>(() => storageService.getActiveExam());
  const [activeTab, setActiveTab] = useState<ActiveTab>('dashboard');
  const [stats, setStats] = useState<UserStats>(() => storageService.getStats(storageService.getActiveExam()));
  const [questions, setQuestions] = useState<Question[]>(() => storageService.getAllQuestions(storageService.getActiveExam()));
  const [currentAttempt, setCurrentAttempt] = useState<ExamAttempt | null>(() => storageService.getLatestExamAttempt(storageService.getActiveExam()));
  const [practiceDomainFilter, setPracticeDomainFilter] = useState<DomainId | 'all'>('all');
  const [practiceTargetQuestionId, setPracticeTargetQuestionId] = useState<string | undefined>(undefined);

  const refreshState = (exam: ExamId = activeExam) => {
    setStats(storageService.getStats(exam));
    setQuestions(storageService.getAllQuestions(exam));
  };

  const handleSwitchExam = (newExam: ExamId) => {
    storageService.setActiveExam(newExam);
    setActiveExam(newExam);
    setStats(storageService.getStats(newExam));
    setQuestions(storageService.getAllQuestions(newExam));
    setCurrentAttempt(storageService.getLatestExamAttempt(newExam));
    setPracticeDomainFilter('all');
    setPracticeTargetQuestionId(undefined);
  };

  const handleFinishExam = (attempt: ExamAttempt) => {
    setCurrentAttempt(attempt);
    refreshState(activeExam);
    setActiveTab('results');
  };

  const handleFilterDomainFromDashboard = (domain?: DomainId | 'all') => {
    setPracticeDomainFilter(domain || 'all');
    setPracticeTargetQuestionId(undefined);
    setActiveTab('practice');
  };

  const handleDrillWeakTopic = (topic: string) => {
    setPracticeDomainFilter('all');
    setPracticeTargetQuestionId(undefined);
    setActiveTab('practice');
  };

  const handleStartDayFromPlan = (dayNumber: number, domainFilter?: DomainId) => {
    setPracticeDomainFilter(domainFilter || 'all');
    setPracticeTargetQuestionId(undefined);
    setActiveTab('practice');
  };

  const handlePracticeSpecificQuestion = (questionId: string) => {
    setPracticeTargetQuestionId(questionId);
    setPracticeDomainFilter('all');
    setActiveTab('practice');
  };

  const handlePracticeAll = () => {
    setPracticeDomainFilter('all');
    setPracticeTargetQuestionId(undefined);
    setActiveTab('practice');
  };

  const handleViewStudyGuide = (domainFilter?: DomainId) => {
    setActiveTab('study-guides');
  };

  return (
    <div className="min-h-screen bg-[#0B101D] text-slate-100 flex flex-col font-sans selection:bg-teal-400 selection:text-slate-950">
      
      {/* Top Navbar with Multi-Exam Switcher */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        stats={stats}
        totalQuestions={questions.length}
        activeExam={activeExam}
        onSwitchExam={handleSwitchExam}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        
        {/* 1. Dashboard */}
        {activeTab === 'dashboard' && (
          <Dashboard
            stats={stats}
            questions={questions}
            totalQuestions={questions.length}
            activeExam={activeExam}
            onSwitchExam={handleSwitchExam}
            setActiveTab={setActiveTab}
            onFilterDomain={handleFilterDomainFromDashboard}
            onSelectAttempt={(attempt) => {
              setCurrentAttempt(attempt);
              setActiveTab('results');
            }}
          />
        )}

        {/* 2. 7-Day Plan (Roadmap) */}
        {activeTab === '7-day-plan' && (
          <SevenDayPlan
            stats={stats}
            questions={questions}
            activeExam={activeExam}
            onStartDay={handleStartDayFromPlan}
            onStartExam={() => setActiveTab('mock-exam')}
            onViewStudyGuide={handleViewStudyGuide}
          />
        )}

        {/* 3. Question Bank (Directory & Filterable Repository) */}
        {activeTab === 'question-bank' && (
          <QuestionBank
            questions={questions}
            stats={stats}
            activeExam={activeExam}
            onPracticeQuestion={handlePracticeSpecificQuestion}
            onPracticeAll={handlePracticeAll}
            onStatsChange={() => refreshState(activeExam)}
          />
        )}

        {/* 4. Practice Mode */}
        {activeTab === 'practice' && (
          <PracticeMode
            questions={questions}
            stats={stats}
            activeExam={activeExam}
            onStatsChange={() => refreshState(activeExam)}
            initialDomainFilter={practiceDomainFilter}
            initialQuestionId={practiceTargetQuestionId}
          />
        )}

        {/* 5. Timed Mock Exam */}
        {activeTab === 'mock-exam' && (
          <MockExam
            questions={questions}
            activeExam={activeExam}
            onFinishExam={handleFinishExam}
            onExitExam={() => setActiveTab('dashboard')}
          />
        )}

        {/* 6. Mistake Review & Weak Point Analysis */}
        {activeTab === 'mistake-review' && (
          <MistakeReview
            questions={questions}
            stats={stats}
            activeExam={activeExam}
            onDrillMistakes={(mistakeIds) => {
              setPracticeDomainFilter('all');
              setPracticeTargetQuestionId(mistakeIds[0]);
              setActiveTab('practice');
            }}
            onStatsChange={() => refreshState(activeExam)}
            onStartPractice={() => {
              setPracticeDomainFilter('all');
              setPracticeTargetQuestionId(undefined);
              setActiveTab('practice');
            }}
          />
        )}

        {/* 7. Exam Results / Scorecard */}
        {activeTab === 'results' && currentAttempt && (
          <ExamResults
            attempt={currentAttempt}
            questions={questions}
            activeExam={activeExam}
            setActiveTab={setActiveTab}
            onRetakeExam={() => setActiveTab('mock-exam')}
            onDrillWeakTopic={handleDrillWeakTopic}
          />
        )}

        {/* 8. Study Guides & Cheat Sheets */}
        {activeTab === 'study-guides' && (
          <StudyGuides
            onPracticeDomain={handleFilterDomainFromDashboard}
            initialDomainFilter={practiceDomainFilter}
            activeExam={activeExam}
          />
        )}

        {/* 9. Importer */}
        {activeTab === 'importer' && (
          <QuestionImporter
            stats={stats}
            onQuestionsUpdated={() => refreshState(activeExam)}
          />
        )}

        {/* 10. Performance Telemetry & Analytics */}
        {activeTab === 'analytics' && (
          <PerformanceAnalytics
            stats={stats}
            questions={questions}
            activeExam={activeExam}
            onStartPractice={handleFilterDomainFromDashboard}
            onStartExam={() => setActiveTab('mock-exam')}
          />
        )}

        {/* 11. Starred & Saved Questions */}
        {activeTab === 'starred' && (
          <StarredQuestions
            questions={questions}
            stats={stats}
            activeExam={activeExam}
            onPracticeQuestion={handlePracticeSpecificQuestion}
            onPracticeAllStarred={(starredIds) => {
              if (starredIds.length > 0) {
                handlePracticeSpecificQuestion(starredIds[0]);
              }
            }}
            onStatsChange={() => refreshState(activeExam)}
          />
        )}

        {/* 12. Application Settings */}
        {activeTab === 'settings' && (
          <SettingsPage
            totalQuestions={questions.length}
            activeExam={activeExam}
            onResetAllData={() => refreshState(activeExam)}
            onOpenImporter={() => setActiveTab('importer')}
          />
        )}

      </main>

      {/* Clean Global Footer */}
      <footer className="border-t border-slate-800/80 bg-[#090D17] py-6 text-center text-xs text-slate-500 mt-12">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Microsoft Fabric Certification Studio &middot; {EXAMS[activeExam].code}: {EXAMS[activeExam].title}</span>
          <span>100% Client-Side &middot; Multi-Exam LocalStorage Saved &middot; No backend required</span>
        </div>
      </footer>

    </div>
  );
};

export default App;
