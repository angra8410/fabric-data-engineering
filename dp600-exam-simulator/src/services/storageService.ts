import { Question, UserStats, ExamAttempt, DomainId } from '../types';
import { STARTER_QUESTIONS } from '../data/dp600Questions';
import { MS_LEARN_50_QUESTIONS } from '../data/mslearnQuestions';

const STATS_KEY = 'dp600_user_stats_v1';

const DEFAULT_STATS: UserStats = {
  streakDays: 1,
  lastStudyDate: new Date().toISOString().split('T')[0],
  totalAnswered: 0,
  correctAnswers: 0,
  answeredQuestionIds: {},
  bookmarkedQuestionIds: [],
  examAttempts: [],
  customQuestions: []
};

export const storageService = {
  getStats(): UserStats {
    try {
      const data = localStorage.getItem(STATS_KEY);
      if (!data) return DEFAULT_STATS;
      const parsed = JSON.parse(data);
      const stats: UserStats = { ...DEFAULT_STATS, ...parsed };

      // Self-healing migration: purge legacy custom questions containing dummy fallback strings
      if (stats.customQuestions && stats.customQuestions.length > 0) {
        const msLearnTexts = new Set(MS_LEARN_50_QUESTIONS.map(q => q.text.trim().toLowerCase()));
        const msLearnIds = new Set(MS_LEARN_50_QUESTIONS.map(q => q.id));
        const cleanCustom = stats.customQuestions.filter(q => {
          if (msLearnIds.has(q.id) || msLearnTexts.has(q.text.trim().toLowerCase())) return false;
          const hasDummy = q.options?.some(opt => 
            opt.text.includes('Use workspace Viewer role') || 
            opt.text.includes('Use DirectQuery mode pointing to SQL analytics') ||
            opt.text.includes('COUNT; MEAN') ||
            opt.text.includes('Configure an Azure Data Factory pipeline with copy')
          );
          return !hasDummy;
        });

        if (cleanCustom.length !== stats.customQuestions.length) {
          stats.customQuestions = cleanCustom;
          try {
            localStorage.setItem(STATS_KEY, JSON.stringify(stats));
          } catch {}
        }
      }

      return stats;
    } catch {
      return DEFAULT_STATS;
    }
  },

  saveStats(stats: UserStats): void {
    try {
      localStorage.setItem(STATS_KEY, JSON.stringify(stats));
    } catch (e) {
      console.error('Failed to save stats to localStorage', e);
    }
  },

  getAllQuestions(): Question[] {
    const stats = this.getStats();
    // Unified built-in bank: Starter + MS Learn 50 Questions
    const baseQuestions = [...STARTER_QUESTIONS, ...MS_LEARN_50_QUESTIONS];
    const baseIds = new Set(baseQuestions.map(q => q.id));
    const customOnly = stats.customQuestions.filter(q => !baseIds.has(q.id));
    return [...baseQuestions, ...customOnly];
  },

  getQuestionById(id: string): Question | undefined {
    return this.getAllQuestions().find(q => q.id === id);
  },

  recordAnswer(questionId: string, optionId: string, isCorrect: boolean): UserStats {
    const stats = this.getStats();
    const today = new Date().toISOString().split('T')[0];

    // Streak calculation
    if (stats.lastStudyDate !== today) {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const yesterdayStr = yesterday.toISOString().split('T')[0];

      if (stats.lastStudyDate === yesterdayStr) {
        stats.streakDays += 1;
      } else {
        stats.streakDays = 1;
      }
      stats.lastStudyDate = today;
    }

    const prevAttempt = stats.answeredQuestionIds[questionId];
    if (!prevAttempt) {
      stats.totalAnswered += 1;
      if (isCorrect) stats.correctAnswers += 1;
    } else {
      if (!prevAttempt.isCorrect && isCorrect) {
        stats.correctAnswers += 1;
      } else if (prevAttempt.isCorrect && !isCorrect) {
        stats.correctAnswers = Math.max(0, stats.correctAnswers - 1);
      }
    }

    stats.answeredQuestionIds[questionId] = {
      answeredOptionId: optionId,
      isCorrect,
      lastAttemptDate: today,
      attemptCount: (prevAttempt?.attemptCount || 0) + 1,
      correctCount: (prevAttempt?.correctCount || 0) + (isCorrect ? 1 : 0)
    };

    this.saveStats(stats);
    return stats;
  },

  resetMistakes(): void {
    const stats = this.getStats();
    Object.keys(stats.answeredQuestionIds).forEach(qId => {
      if (!stats.answeredQuestionIds[qId].isCorrect) {
        delete stats.answeredQuestionIds[qId];
      }
    });
    this.saveStats(stats);
  },

  toggleBookmark(questionId: string): boolean {
    const stats = this.getStats();
    const index = stats.bookmarkedQuestionIds.indexOf(questionId);
    let bookmarked = false;

    if (index === -1) {
      stats.bookmarkedQuestionIds.push(questionId);
      bookmarked = true;
    } else {
      stats.bookmarkedQuestionIds.splice(index, 1);
      bookmarked = false;
    }

    this.saveStats(stats);
    return bookmarked;
  },

  isBookmarked(questionId: string): boolean {
    const stats = this.getStats();
    return stats.bookmarkedQuestionIds.includes(questionId);
  },

  saveExamAttempt(attempt: ExamAttempt): void {
    const stats = this.getStats();
    stats.examAttempts.unshift(attempt);
    // update answers from exam
    Object.entries(attempt.userAnswers).forEach(([qId, ansOpt]) => {
      const q = this.getQuestionById(qId);
      if (q) {
        let isCorrect = false;
        if (q.type === 'drag_and_drop') {
          isCorrect = JSON.stringify(q.correctOrder) === ansOpt;
        } else if (q.type === 'multi_select' || (q.correctOptionIds && q.correctOptionIds.length > 1)) {
          const correctList = (q.correctOptionIds || [q.correctOptionId]).slice().sort();
          let userList: string[] = [];
          try {
            const parsed = JSON.parse(ansOpt);
            if (Array.isArray(parsed)) userList = parsed.map(String).sort();
            else userList = String(ansOpt).split(',').map(s => s.trim()).filter(Boolean).sort();
          } catch {
            userList = String(ansOpt).split(',').map(s => s.trim()).filter(Boolean).sort();
          }
          isCorrect = JSON.stringify(correctList) === JSON.stringify(userList);
        } else {
          isCorrect = q.correctOptionId === ansOpt;
        }
        this.recordAnswer(qId, ansOpt, isCorrect);
      }
    });
    this.saveStats(stats);
  },

  getExamAttempts(): ExamAttempt[] {
    return this.getStats().examAttempts;
  },

  getLatestExamAttempt(): ExamAttempt | null {
    const attempts = this.getExamAttempts();
    return attempts.length > 0 ? attempts[0] : null;
  },

  addCustomQuestions(newQuestions: Question[]): number {
    const stats = this.getStats();
    // avoid duplicates by ID or identical question text
    const existingIds = new Set([...STARTER_QUESTIONS.map(q => q.id), ...stats.customQuestions.map(q => q.id)]);
    const existingTexts = new Set([
      ...STARTER_QUESTIONS.map(q => q.text.trim().toLowerCase()),
      ...stats.customQuestions.map(q => q.text.trim().toLowerCase())
    ]);

    const unique = newQuestions.filter(q => 
      !existingIds.has(q.id) && !existingTexts.has(q.text.trim().toLowerCase())
    );
    stats.customQuestions.push(...unique);
    this.saveStats(stats);
    return unique.length;
  },

  deleteCustomQuestion(questionId: string): void {
    const stats = this.getStats();
    stats.customQuestions = stats.customQuestions.filter(q => q.id !== questionId);
    delete stats.answeredQuestionIds[questionId];
    stats.bookmarkedQuestionIds = stats.bookmarkedQuestionIds.filter(id => id !== questionId);
    this.saveStats(stats);
  },

  resetAllData(): void {
    localStorage.removeItem(STATS_KEY);
  },

  clearAllData(): void {
    this.resetAllData();
  },

  exportBackupJson(): string {
    const stats = this.getStats();
    return JSON.stringify({
      version: 'dp600-backup-v1',
      exportDate: new Date().toISOString(),
      stats
    }, null, 2);
  }
};
