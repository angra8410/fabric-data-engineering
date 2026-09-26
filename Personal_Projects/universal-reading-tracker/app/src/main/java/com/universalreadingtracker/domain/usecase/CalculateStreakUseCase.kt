package com.universalreadingtracker.domain.usecase

import com.universalreadingtracker.domain.model.DailyReadingSummary
import com.universalreadingtracker.domain.model.StreakInfo
import java.time.LocalDate
import java.time.format.DateTimeFormatter

/**
 * Implements RF-08 and RF-09 from spec.md:
 * Calculates the current active streak and longest streak based on valid reading days.
 * A day is valid if totalMinutesRead >= 1 or is marked as isHistoricalBackfill.
 */
class CalculateStreakUseCase {

    private val dateFormatter = DateTimeFormatter.ISO_LOCAL_DATE

    operator fun invoke(summaries: List<DailyReadingSummary>, today: LocalDate = LocalDate.now()): StreakInfo {
        if (summaries.isEmpty()) {
            return StreakInfo(0, 0, false, 0)
        }

        // Map summaries by date string
        val summaryByDate = summaries.associateBy { it.date }

        val todayString = today.format(dateFormatter)
        val todaySummary = summaryByDate[todayString]
        val isTodayActive = todaySummary?.isValidStreakDay == true

        var currentStreak = 0
        var checkDate = if (isTodayActive) today else today.minusDays(1)

        // Iterate backwards from the anchor date to count consecutive valid days
        while (true) {
            val dateStr = checkDate.format(dateFormatter)
            val summary = summaryByDate[dateStr]
            if (summary != null && summary.isValidStreakDay) {
                currentStreak++
                checkDate = checkDate.minusDays(1)
            } else {
                break
            }
        }

        val totalValidDays = summaries.count { it.isValidStreakDay }
        val longestStreak = maxOf(currentStreak, totalValidDays)

        return StreakInfo(
            currentStreakDays = currentStreak,
            longestStreakDays = longestStreak,
            isStreakActiveToday = isTodayActive,
            totalHistoricalDays = totalValidDays
        )
    }
}
