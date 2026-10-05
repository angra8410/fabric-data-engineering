import { Question, UserStats, ExamAttempt, ExamId } from '../types';
import { STARTER_QUESTIONS } from '../data/dp600Questions';
import { MS_LEARN_50_QUESTIONS } from '../data/mslearnQuestions';
import { DP700_QUESTIONS } from '../data/dp700Questions';

const ACTIVE_EXAM_KEY = 'fabric_active_exam';

function getStatsKey(examId: ExamId): string {
  return examId === 'dp600' ? 'dp600_user_stats_v1' : 'dp700_user_stats_v1';
}

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

class StorageServiceImpl {
  getActiveExam(): ExamId {
    try {
      const saved = localStorage.getItem(ACTIVE_EXAM_KEY);
      if (saved === 'dp600' || saved === 'dp700') return saved;
    } catch {}
    return 'dp700'; // Default to newest DP-700
  }

  setActiveExam(examId: ExamId): void {
    try {
      localStorage.setItem(ACTIVE_EXAM_KEY, examId);
    } catch (e) {
      console.error('Failed to save active exam', e);
    }
  }

  getStats(examId?: ExamId): UserStats {
    const targetExam = examId || this.getActiveExam();
    const key = getStatsKey(targetExam);
    try {
      const data = localStorage.getItem(key);
      if (!data) return { ...DEFAULT_STATS };
      const parsed = JSON.parse(data);
      const stats: UserStats = { ...DEFAULT_STATS, ...parsed };

      // Self-healing migration: purge legacy custom questions containing dummy fallback strings
      if (targetExam === 'dp600' && stats.customQuestions && stats.customQuestions.length > 0) {
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
            localStorage.setItem(key, JSON.stringify(stats));
          } catch {}
        }
      }

      return stats;
    } catch {
      return { ...DEFAULT_STATS };
    }
  }

  saveStats(stats: UserStats, examId?: ExamId): void {
    const targetExam = examId || this.getActiveExam();
    const key = getStatsKey(targetExam);
    try {
      localStorage.setItem(key, JSON.stringify(stats));
    } catch (e) {
      console.error(`Failed to save stats to localStorage for ${key}`, e);
    }
  }

  getAllQuestions(examId?: ExamId): Question[] {
    const targetExam = examId || this.getActiveExam();
    const stats = this.getStats(targetExam);
    if (targetExam === 'dp700') {
      const baseQuestions = DP700_QUESTIONS;
      const baseIds = new Set(baseQuestions.map(q => q.id));
      const customOnly = stats.customQuestions.filter(q => !baseIds.has(q.id));
      return [...baseQuestions, ...customOnly];
    } else {
      const baseQuestions = [...STARTER_QUESTIONS, ...MS_LEARN_50_QUESTIONS];
      const baseIds = new Set(baseQuestions.map(q => q.id));
      const customOnly = stats.customQuestions.filter(q => !baseIds.has(q.id));
      return [...baseQuestions, ...customOnly];
    }
  }

  getQuestionById(id: string, examId?: ExamId): Question | undefined {
    const targetExam = examId || this.getActiveExam();
    const currentList = this.getAllQuestions(targetExam);
    const found = currentList.find(q => q.id === id);
    if (found) return found;
    // Cross-exam lookup fallback
    const otherExam: ExamId = targetExam === 'dp700' ? 'dp600' : 'dp700';
    return this.getAllQuestions(otherExam).find(q => q.id === id);
  }

  recordAnswer(questionId: string, optionId: string, isCorrect: boolean, examId?: ExamId): UserStats {
    const targetExam = examId || this.getActiveExam();
    const stats = this.getStats(targetExam);
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

    this.saveStats(stats, targetExam);
    return stats;
  }

  resetMistakes(examId?: ExamId): void {
    const targetExam = examId || this.getActiveExam();
    const stats = this.getStats(targetExam);
    Object.keys(stats.answeredQuestionIds).forEach(qId => {
      if (!stats.answeredQuestionIds[qId].isCorrect) {
        delete stats.answeredQuestionIds[qId];
      }
    });
    this.saveStats(stats, targetExam);
  }

  toggleBookmark(questionId: string, examId?: ExamId): boolean {
    const targetExam = examId || this.getActiveExam();
    const stats = this.getStats(targetExam);
    const index = stats.bookmarkedQuestionIds.indexOf(questionId);
    let bookmarked = false;

    if (index === -1) {
      stats.bookmarkedQuestionIds.push(questionId);
      bookmarked = true;
    } else {
      stats.bookmarkedQuestionIds.splice(index, 1);
      bookmarked = false;
    }

    this.saveStats(stats, targetExam);
    return bookmarked;
  }

  isBookmarked(questionId: string, examId?: ExamId): boolean {
    const targetExam = examId || this.getActiveExam();
    const stats = this.getStats(targetExam);
    return stats.bookmarkedQuestionIds.includes(questionId);
  }

  saveExamAttempt(attempt: ExamAttempt, examId?: ExamId): void {
    const targetExam = examId || this.getActiveExam();
    const stats = this.getStats(targetExam);
    attempt.examId = targetExam;
    stats.examAttempts.unshift(attempt);
    // update answers from exam
    Object.entries(attempt.userAnswers).forEach(([qId, ansOpt]) => {
      const q = this.getQuestionById(qId, targetExam);
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
        this.recordAnswer(qId, ansOpt, isCorrect, targetExam);
      }
    });
    this.saveStats(stats, targetExam);
  }

  getExamAttempts(examId?: ExamId): ExamAttempt[] {
    const targetExam = examId || this.getActiveExam();
    return this.getStats(targetExam).examAttempts;
  }

  getLatestExamAttempt(examId?: ExamId): ExamAttempt | null {
    const targetExam = examId || this.getActiveExam();
    const attempts = this.getExamAttempts(targetExam);
    return attempts.length > 0 ? attempts[0] : null;
  }

  addCustomQuestions(newQuestions: Question[], examId?: ExamId): number {
    const targetExam = examId || this.getActiveExam();
    const stats = this.getStats(targetExam);
    const existing = this.getAllQuestions(targetExam);
    const existingIds = new Set(existing.map(q => q.id));
    const existingTexts = new Set(existing.map(q => q.text.trim().toLowerCase()));

    const unique = newQuestions
      .map(q => ({ ...q, examId: targetExam }))
      .filter(q => !existingIds.has(q.id) && !existingTexts.has(q.text.trim().toLowerCase()));

    stats.customQuestions.push(...unique);
    this.saveStats(stats, targetExam);
    return unique.length;
  }

  deleteCustomQuestion(questionId: string, examId?: ExamId): void {
    const targetExam = examId || this.getActiveExam();
    const stats = this.getStats(targetExam);
    stats.customQuestions = stats.customQuestions.filter(q => q.id !== questionId);
    delete stats.answeredQuestionIds[questionId];
    stats.bookmarkedQuestionIds = stats.bookmarkedQuestionIds.filter(id => id !== questionId);
    this.saveStats(stats, targetExam);
  }

  resetAllData(examId?: ExamId): void {
    if (examId) {
      localStorage.removeItem(getStatsKey(examId));
    } else {
      localStorage.removeItem(getStatsKey('dp600'));
      localStorage.removeItem(getStatsKey('dp700'));
    }
  }

  clearAllData(examId?: ExamId): void {
    this.resetAllData(examId);
  }

  exportBackupJson(examId?: ExamId): string {
    const targetExam = examId || this.getActiveExam();
    const stats = this.getStats(targetExam);
    return JSON.stringify({
      version: `${targetExam}-backup-v1`,
      examId: targetExam,
      exportDate: new Date().toISOString(),
      stats
    }, null, 2);
  }
}

export const storageService = new StorageServiceImpl();
