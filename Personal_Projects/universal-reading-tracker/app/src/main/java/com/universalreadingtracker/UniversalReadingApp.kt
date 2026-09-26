package com.universalreadingtracker

import android.app.Application
import com.universalreadingtracker.data.local.AppDatabase
import com.universalreadingtracker.data.repository.StreakRepositoryImpl
import com.universalreadingtracker.domain.usecase.BackfillHistoricalStreakUseCase
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.time.LocalDate

/**
 * Main Application class for Universal Reading Tracker.
 * Implements ADR-009: Automatically triggers the 163-day streak backfill on startup if not already seeded.
 */
class UniversalReadingApp : Application() {

    val database by lazy { AppDatabase.getInstance(this) }
    private val appScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onCreate() {
        super.onCreate()
        ensureHistoricalStreakBackfill()
    }

    private fun ensureHistoricalStreakBackfill() {
        appScope.launch {
            val streakRepo = StreakRepositoryImpl(database.dailyReadingSummaryDao())
            if (!streakRepo.hasCompletedBackfill()) {
                // Implements RF-08 & ADR-009: Backfill the user's hard-earned 163-day reading streak
                val backfillUseCase = BackfillHistoricalStreakUseCase(streakRepo)
                backfillUseCase(streakDays = 163, referenceDate = LocalDate.now())
            }
        }
    }
}
