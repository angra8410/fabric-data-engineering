package com.universalreadingtracker.domain.repository

import com.universalreadingtracker.domain.model.StreakInfo
import kotlinx.coroutines.flow.Flow

interface StreakRepository {
    fun getStreakInfo(): Flow<StreakInfo>
    suspend fun backfillHistoricalStreak(streakDays: Int, referenceDate: String)
    suspend fun hasCompletedBackfill(): Boolean
}
