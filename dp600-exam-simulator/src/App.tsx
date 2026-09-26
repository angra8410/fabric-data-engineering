import React, { useState } from 'react';
import { storageService } from './services/storageService';
import { Question, UserStats, ExamAttempt, DomainId } from './types';
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
  const [activeTab, setActiveTab] = useState<ActiveTab>('dashboard');
  const [stats, setStats] = useState<UserStats>(() => storageService.getStats());
  const [questions, setQuestions] = useState<Question[]>(() => storageService.getAllQuestions());
  const [currentAttempt, setCurrentAttempt] = useState<ExamAttempt | null>(() => storageService.getLatestExamAttempt());
  const [practiceDomainFilter, setPracticeDomainFilter] = useState<DomainId | 'all'>('all');
  const [practiceTargetQuestionId, setPracticeTargetQuestionId] = useState<string | undefined>(undefined);

  const refreshState = () => {
    setStats(storageService.getStats());
    setQuestions(storageService.getAllQuestions());
  };

  const handleFinishExam = (attempt: ExamAttempt) => {
    setCurrentAttempt(attempt);
    refreshState();
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
      
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        stats={stats}
        totalQuestions={questions.length}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        
        {/* 1. Dashboard */}
        {activeTab === 'dashboard' && (
          <Dashboard
            stats={stats}
            questions={questions}
            totalQuestions={questions.length}
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
            onPracticeQuestion={handlePracticeSpecificQuestion}
            onPracticeAll={handlePracticeAll}
            onStatsChange={refreshState}
          />
        )}

        {/* 4. Practice Mode */}
        {activeTab === 'practice' && (
          <PracticeMode
            questions={questions}
            stats={stats}
            onStatsChange={refreshState}
            initialDomainFilter={practiceDomainFilter}
            initialQuestionId={practiceTargetQuestionId}
          />
        )}

        {/* 5. Timed Mock Exam */}
        {activeTab === 'mock-exam' && (
          <MockExam
            questions={questions}
            onFinishExam={handleFinishExam}
            onExitExam={() => setActiveTab('dashboard')}
          />
        )}

        {/* 6. Mistake Review & Weak Point Analysis (Screenshot 3) */}
        {activeTab === 'mistake-review' && (
          <MistakeReview
            questions={questions}
            stats={stats}
            onDrillMistakes={(mistakeIds) => {
              setPracticeDomainFilter('all');
              setPracticeTargetQuestionId(mistakeIds[0]);
              setActiveTab('practice');
            }}
            onStatsChange={refreshState}
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
            setActiveTab={setActiveTab}
            onRetakeExam={() => setActiveTab('mock-exam')}
            onDrillWeakTopic={handleDrillWeakTopic}
          />
        )}

        {/* 7. Study Guides & Cheat Sheets */}
        {activeTab === 'study-guides' && (
          <StudyGuides
            onPracticeDomain={handleFilterDomainFromDashboard}
            initialDomainFilter={practiceDomainFilter}
          />
        )}

        {/* 8. Importer */}
        {activeTab === 'importer' && (
          <QuestionImporter
            stats={stats}
            onQuestionsUpdated={refreshState}
          />
        )}

        {/* 9. Performance Telemetry & Analytics (Screenshot 1 & 2) */}
        {activeTab === 'analytics' && (
          <PerformanceAnalytics
            stats={stats}
            questions={questions}
            onStartPractice={handleFilterDomainFromDashboard}
            onStartExam={() => setActiveTab('mock-exam')}
          />
        )}

        {/* 10. Starred & Saved Questions */}
        {activeTab === 'starred' && (
          <StarredQuestions
            questions={questions}
            stats={stats}
            onPracticeQuestion={handlePracticeSpecificQuestion}
            onPracticeAllStarred={(starredIds) => {
              if (starredIds.length > 0) {
                handlePracticeSpecificQuestion(starredIds[0]);
              }
            }}
            onStatsChange={refreshState}
          />
        )}

        {/* 11. Application Settings (Screenshot 3) */}
        {activeTab === 'settings' && (
          <SettingsPage
            totalQuestions={questions.length}
            onResetAllData={refreshState}
            onOpenImporter={() => setActiveTab('importer')}
          />
        )}

      </main>

      {/* Clean Global Footer */}
      <footer className="border-t border-slate-800/80 bg-[#090D17] py-6 text-center text-xs text-slate-500 mt-12">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Microsoft Certified: Fabric Analytics Engineer Associate (DP-600) Simulator</span>
          <span>100% Client-Side · LocalStorage Saved · No backend required</span>
        </div>
      </footer>

    </div>
  );
};

export default App;
