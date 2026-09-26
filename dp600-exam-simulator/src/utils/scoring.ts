import { Question, ExamAttempt, DomainId, DOMAINS } from '../types';

export function calculateExamScore(
  questions: Question[],
  userAnswers: Record<string, string>,
  timeSpentSeconds: number,
  flaggedQuestionIds: string[]
): ExamAttempt {
  let correctCount = 0;
  const domainTotals: Record<DomainId, { total: number; correct: number; percentage: number }> = {
    domain1: { total: 0, correct: 0, percentage: 0 },
    domain2: { total: 0, correct: 0, percentage: 0 },
    domain3: { total: 0, correct: 0, percentage: 0 }
  };

  const topicTotals: Record<string, { total: number; correct: number }> = {};

  questions.forEach(q => {
    const userAnswer = userAnswers[q.id];
    let isCorrect = false;
    if (q.type === 'drag_and_drop') {
      isCorrect = !!userAnswer && JSON.stringify(q.correctOrder) === userAnswer;
    } else if (q.type === 'multi_select' || (q.correctOptionIds && q.correctOptionIds.length > 1)) {
      const correctList = (q.correctOptionIds || [q.correctOptionId]).slice().sort();
      let userList: string[] = [];
      if (userAnswer) {
        try {
          const parsed = JSON.parse(userAnswer);
          if (Array.isArray(parsed)) {
            userList = parsed.map(String).sort();
          } else {
            userList = String(userAnswer).split(',').map(s => s.trim()).filter(Boolean).sort();
          }
        } catch {
          userList = String(userAnswer).split(',').map(s => s.trim()).filter(Boolean).sort();
        }
      }
      isCorrect = JSON.stringify(correctList) === JSON.stringify(userList);
    } else {
      isCorrect = userAnswer === q.correctOptionId;
    }

    if (isCorrect) correctCount++;

    // Domain tracking
    if (domainTotals[q.domain]) {
      domainTotals[q.domain].total++;
      if (isCorrect) domainTotals[q.domain].correct++;
    }

    // Topic tracking
    if (!topicTotals[q.topic]) {
      topicTotals[q.topic] = { total: 0, correct: 0 };
    }
    topicTotals[q.topic].total++;
    if (isCorrect) topicTotals[q.topic].correct++;
  });

  // Calculate domain percentages
  (Object.keys(domainTotals) as DomainId[]).forEach(d => {
    const item = domainTotals[d];
    item.percentage = item.total > 0 ? Math.round((item.correct / item.total) * 100) : 0;
  });

  // Identify weak topics (< 70% accuracy)
  const weakTopics = Object.entries(topicTotals)
    .filter(([_, data]) => (data.correct / data.total) < 0.70)
    .map(([topic]) => topic);

  // Scaled Score (200 - 1000, pass threshold 700)
  // Weighted by official DP-600 domain distribution
  const w1 = DOMAINS.domain1.minWeight + (DOMAINS.domain1.maxWeight - DOMAINS.domain1.minWeight) / 2; // ~0.125
  const w2 = DOMAINS.domain2.minWeight + (DOMAINS.domain2.maxWeight - DOMAINS.domain2.minWeight) / 2; // ~0.425
  const w3 = DOMAINS.domain3.minWeight + (DOMAINS.domain3.maxWeight - DOMAINS.domain3.minWeight) / 2; // ~0.425

  let weightedAccuracy = 0;
  if (questions.length > 0) {
    const acc1 = domainTotals.domain1.total > 0 ? domainTotals.domain1.correct / domainTotals.domain1.total : (correctCount / questions.length);
    const acc2 = domainTotals.domain2.total > 0 ? domainTotals.domain2.correct / domainTotals.domain2.total : (correctCount / questions.length);
    const acc3 = domainTotals.domain3.total > 0 ? domainTotals.domain3.correct / domainTotals.domain3.total : (correctCount / questions.length);

    weightedAccuracy = (acc1 * w1) + (acc2 * w2) + (acc3 * w3);
  }

  const rawScaled = Math.round(200 + 800 * weightedAccuracy);
  const score = Math.min(1000, Math.max(200, rawScaled));
  const passed = score >= 700;

  return {
    id: `exam-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
    timestamp: new Date().toISOString(),
    score,
    passed,
    totalQuestions: questions.length,
    correctCount,
    timeSpentSeconds,
    domainScores: domainTotals,
    userAnswers,
    flaggedQuestionIds,
    questionIds: questions.map(q => q.id),
    weakTopics
  };
}
