package com.universalreadingtracker.data.repository

import com.universalreadingtracker.data.local.dao.DailyReadingSummaryDao
import com.universalreadingtracker.data.local.entity.DailyReadingSummaryEntity
import com.universalreadingtracker.domain.model.StreakInfo
import com.universalreadingtracker.domain.repository.StreakRepository
import com.universalreadingtracker.domain.usecase.CalculateStreakUseCase
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.time.LocalDate
import java.time.format.DateTimeFormatter

/**
 * Implements RF-08, RF-09 and ADR-009 from spec.md & decisions.md:
 * Manages streak calculation and populates historical backfill (163 days up to today).
 */
class StreakRepositoryImpl(
    private val summaryDao: DailyReadingSummaryDao,
    private val calculateStreakUseCase: CalculateStreakUseCase = CalculateStreakUseCase()
) : StreakRepository {

    private val dateFormatter = DateTimeFormatter.ISO_LOCAL_DATE

    override fun getStreakInfo(): Flow<StreakInfo> {
        return summaryDao.getDailySummaries(limitDays = 730).map { entities ->
            val domainSummaries = entities.map { it.toDomain() }
            calculateStreakUseCase(domainSummaries, LocalDate.now())
        }
    }

    override suspend fun backfillHistoricalStreak(streakDays: Int, referenceDate: String) {
        val targetDate = LocalDate.parse(referenceDate, dateFormatter)
        
        // Remove any historical backfill entry for today so today starts fresh
        summaryDao.deleteHistoricalBackfillForDate(referenceDate)

        val entitiesToInsert = mutableListOf<DailyReadingSummaryEntity>()

        // Generate consecutive daily summaries backwards starting from YESTERDAY (i = 1)
        for (i in 1..streakDays) {
            val pastDate = targetDate.minusDays(i.toLong())
            val dateStr = pastDate.format(dateFormatter)

            val existing = summaryDao.getSummaryForDate(dateStr)
            if (existing == null) {
                entitiesToInsert.add(
                    DailyReadingSummaryEntity(
                        date = dateStr,
                        totalMinutesRead = 30, // Seeded representative historical session
                        audioMinutes = 15,
                        kindleMinutes = 15,
                        physicalMinutes = 0,
                        goalReached = true,
                        isHistoricalBackfill = true
                    )
                )
            }
        }

        if (entitiesToInsert.isNotEmpty()) {
            summaryDao.insertAll(entitiesToInsert)
        }
    }

    override suspend fun hasCompletedBackfill(): Boolean {
        return summaryDao.countHistoricalBackfillDays() >= 163
    }
}
