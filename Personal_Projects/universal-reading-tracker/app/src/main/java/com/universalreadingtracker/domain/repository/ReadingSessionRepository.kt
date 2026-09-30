package com.universalreadingtracker.domain.repository

import com.universalreadingtracker.domain.model.DailyReadingSummary
import com.universalreadingtracker.domain.model.ReadingSession
import kotlinx.coroutines.flow.Flow

interface ReadingSessionRepository {
    fun getAllSessions(): Flow<List<ReadingSession>>
    fun getSessionsForDate(dateString: String): Flow<List<ReadingSession>>
    suspend fun insertSession(session: ReadingSession): Long
    suspend fun getDailySummaries(limitDays: Int = 365): Flow<List<DailyReadingSummary>>
    suspend fun getSummaryForDate(dateString: String): DailyReadingSummary?
    fun observeSummaryForDate(dateString: String): Flow<DailyReadingSummary?>
    suspend fun saveDailySummary(summary: DailyReadingSummary)
    suspend fun autoRepairThrottledSessions()
    suspend fun recalculateDailySummaryForDate(dateString: String)
    suspend fun updateSessionNotes(sessionId: Long, notes: String)
}
