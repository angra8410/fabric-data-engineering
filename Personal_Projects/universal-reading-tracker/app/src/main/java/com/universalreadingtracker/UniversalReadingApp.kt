package com.universalreadingtracker

import android.app.Application
import com.universalreadingtracker.data.local.AppDatabase
import com.universalreadingtracker.data.repository.StreakRepositoryImpl
import com.universalreadingtracker.domain.usecase.BackfillHistoricalStreakUseCase
import com.universalreadingtracker.receiver.ReadingReminderScheduler
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.format.DateTimeFormatter

/**
 * Main Application class for Universal Reading Tracker.
 * Implements ADR-009 & ADR-015: Automatically triggers the 164-day streak backfill up to yesterday,
 * ensuring today starts fresh with actual user reading.
 */
class UniversalReadingApp : Application() {

    val database by lazy { AppDatabase.getInstance(this) }
    private val appScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onCreate() {
        super.onCreate()
        ensureHistoricalStreakBackfill()
        ReadingReminderScheduler.scheduleDailyReminder(this)
    }

    private fun ensureHistoricalStreakBackfill() {
        appScope.launch {
            val todayStr = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE)
            // Clear any accidental backfill dummy data on today so today reflects real reading
            database.dailyReadingSummaryDao().deleteHistoricalBackfillForDate(todayStr)

            val streakRepo = StreakRepositoryImpl(database.dailyReadingSummaryDao())
            if (!streakRepo.hasCompletedBackfill()) {
                val backfillUseCase = BackfillHistoricalStreakUseCase(streakRepo)
                backfillUseCase(streakDays = 164, referenceDate = LocalDate.now())
            }
        }
    }
}
