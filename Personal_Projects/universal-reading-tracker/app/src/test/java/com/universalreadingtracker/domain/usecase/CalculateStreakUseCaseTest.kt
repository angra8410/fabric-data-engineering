package com.universalreadingtracker.domain.usecase

import com.universalreadingtracker.domain.model.DailyReadingSummary
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDate

/**
 * Unit tests verifying RF-08 and RF-09: Streak calculation with 163-day backfill.
 */
class CalculateStreakUseCaseTest {

    private val useCase = CalculateStreakUseCase()
    private val today = LocalDate.of(2026, 9, 26)

    @Test
    fun streakWith163BackfillDays_yields163CurrentStreak() {
        val summaries = mutableListOf<DailyReadingSummary>()

        // Seed 163 days backfill
        for (i in 0 until 163) {
            val dateStr = today.minusDays(i.toLong()).toString()
            summaries.add(
                DailyReadingSummary(
                    date = dateStr,
                    totalMinutesRead = 30,
                    audioMinutes = 15,
                    kindleMinutes = 15,
                    physicalMinutes = 0,
                    goalReached = true,
                    isHistoricalBackfill = true
                )
            )
        }

        val streakInfo = useCase(summaries, today)
        assertEquals(163, streakInfo.currentStreakDays)
        assertTrue(streakInfo.isStreakActiveToday)
    }

    @Test
    fun streakIncreasesTo164_whenReadingTomorrow() {
        val summaries = mutableListOf<DailyReadingSummary>()

        // 163 days up to today
        for (i in 0 until 163) {
            val dateStr = today.minusDays(i.toLong()).toString()
            summaries.add(
                DailyReadingSummary(
                    date = dateStr,
                    totalMinutesRead = 30,
                    audioMinutes = 15,
                    kindleMinutes = 15,
                    physicalMinutes = 0,
                    goalReached = true,
                    isHistoricalBackfill = true
                )
            )
        }

        // Add 1 valid session tomorrow (2026-09-27)
        val tomorrow = today.plusDays(1)
        summaries.add(
            DailyReadingSummary(
                date = tomorrow.toString(),
                totalMinutesRead = 25,
                audioMinutes = 25,
                kindleMinutes = 0,
                physicalMinutes = 0,
                goalReached = false,
                isHistoricalBackfill = false
            )
        )

        val streakInfo = useCase(summaries, tomorrow)
        assertEquals(164, streakInfo.currentStreakDays)
        assertTrue(streakInfo.isStreakActiveToday)
    }
}
