package com.universalreadingtracker.presentation.dashboard

import com.universalreadingtracker.domain.model.Book
import com.universalreadingtracker.domain.model.DailyReadingSummary
import com.universalreadingtracker.domain.model.ReadingAnalytics
import com.universalreadingtracker.domain.model.ReadingSession
import com.universalreadingtracker.domain.model.StreakInfo

/**
 * UI State for the Dashboard screen.
 */
data class DashboardState(
    val streakInfo: StreakInfo = StreakInfo(164, 164, false, 164),
    val todaySummary: DailyReadingSummary? = null,
    val recentSessions: List<ReadingSession> = emptyList(),
    val allDailySummaries: List<DailyReadingSummary> = emptyList(),
    val activeBooks: List<Book> = emptyList(),
    val activeBook: Book? = null,
    val analytics: ReadingAnalytics? = null,
    val isAudibleTrackingActive: Boolean = true,
    val isKindleTimerRunning: Boolean = false,
    val kindleTimerElapsedSeconds: Long = 0L,
    val dailyGoalMinutes: Int = 30
)
