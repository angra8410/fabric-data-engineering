package com.universalreadingtracker.domain.usecase

import com.universalreadingtracker.domain.model.Book
import com.universalreadingtracker.domain.model.DailyReadingSummary
import com.universalreadingtracker.domain.model.DayContribution
import com.universalreadingtracker.domain.model.DayModalityItem
import com.universalreadingtracker.domain.model.ReadingAnalytics
import com.universalreadingtracker.domain.model.ReadingRhythmInsights
import com.universalreadingtracker.domain.model.ReadingSession
import com.universalreadingtracker.domain.model.TimeOfDaySlot
import com.universalreadingtracker.domain.model.WeeklyModalityDistribution
import java.time.DayOfWeek
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.temporal.TemporalAdjusters

/**
 * Implements RF-16 and ADR-020:
 * Aggregates annual reading consistency heatmap, weekly modality comparison (Audible vs. Kindle),
 * reading speed rhythm (pages/hour) and preferred time of day insights.
 */
class CalculateReadingAnalyticsUseCase {

    private val dateFormatter = DateTimeFormatter.ISO_LOCAL_DATE

    operator fun invoke(
        summaries: List<DailyReadingSummary>,
        sessions: List<ReadingSession>,
        activeBook: Book? = null,
        today: LocalDate = LocalDate.now(),
        zoneId: ZoneId = ZoneId.systemDefault()
    ): ReadingAnalytics {
        val summaryByDate = summaries.associateBy { it.date }

        // 1. Build heatmap contributions
        val contributions = mutableMapOf<String, DayContribution>()
        var totalMinutes = 0
        var totalValidDays = 0

        for (summary in summaries) {
            val totalMins = summary.totalMinutesRead
            totalMinutes += totalMins
            if (summary.isValidStreakDay) totalValidDays++

            val level = when {
                totalMins <= 0 -> 0
                totalMins <= 15 -> 1
                totalMins <= 30 -> 2
                totalMins <= 60 -> 3
                else -> 4
            }

            contributions[summary.date] = DayContribution(
                date = summary.date,
                totalMinutes = totalMins,
                audioMinutes = summary.audioMinutes,
                kindleMinutes = summary.kindleMinutes,
                physicalMinutes = summary.physicalMinutes,
                intensityLevel = level
            )
        }

        val totalHours = totalMinutes / 60.0f
        val consistencyPct = if (totalValidDays > 0) minOf(100, (totalValidDays * 100) / 365) else 0

        // 2. Weekly Modality Distribution for Current Week (Monday to Sunday)
        val monday = today.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY))
        val weekDayLabels = listOf("L", "M", "M", "J", "V", "S", "D")
        val weekItems = mutableListOf<DayModalityItem>()

        var weekAudioMins = 0
        var weekKindleMins = 0

        for (i in 0..6) {
            val date = monday.plusDays(i.toLong())
            val dateStr = date.format(dateFormatter)
            val daySummary = summaryByDate[dateStr]

            val audio = daySummary?.audioMinutes ?: 0
            val kindle = daySummary?.kindleMinutes ?: 0
            val total = daySummary?.totalMinutesRead ?: 0

            weekAudioMins += audio
            weekKindleMins += kindle

            val isToday = date == today
            val isFuture = date.isAfter(today)

            weekItems.add(
                DayModalityItem(
                    dayLabel = weekDayLabels[i],
                    date = dateStr,
                    audioMinutes = audio,
                    kindleMinutes = kindle,
                    totalMinutes = total,
                    isToday = isToday,
                    isFuture = isFuture
                )
            )
        }

        val totalWeekMins = weekAudioMins + weekKindleMins
        val audioPct = if (totalWeekMins > 0) (weekAudioMins * 100) / totalWeekMins else 0
        val kindlePct = if (totalWeekMins > 0) (weekKindleMins * 100) / totalWeekMins else 0

        val weeklyDistribution = WeeklyModalityDistribution(
            weekDays = weekItems,
            totalAudioMinutes = weekAudioMins,
            totalKindleMinutes = weekKindleMins,
            audioPercentage = audioPct,
            kindlePercentage = kindlePct
        )

        // 3. Rhythm and Peak Time Slot
        var totalPages = 0
        val validPphList = mutableListOf<Float>()
        val slotCounts = mutableMapOf(
            TimeOfDaySlot.MORNING to 0,
            TimeOfDaySlot.AFTERNOON to 0,
            TimeOfDaySlot.NIGHT to 0,
            TimeOfDaySlot.DAWN to 0
        )

        for (s in sessions) {
            val pages = s.pagesRead ?: 0
            if (pages > 0) {
                totalPages += pages
                if (s.realDurationSeconds >= 60) {
                    val pph = (pages * 3600f) / s.realDurationSeconds.toFloat()
                    if (pph in 5f..150f) {
                        validPphList.add(pph)
                    }
                }
            }

            val hour = Instant.ofEpochMilli(s.startTime).atZone(zoneId).hour
            val slot = when (hour) {
                in 6..11 -> TimeOfDaySlot.MORNING
                in 12..17 -> TimeOfDaySlot.AFTERNOON
                in 18..23 -> TimeOfDaySlot.NIGHT
                else -> TimeOfDaySlot.DAWN
            }
            slotCounts[slot] = (slotCounts[slot] ?: 0) + 1
        }

        val avgPagesPerHour = if (validPphList.isNotEmpty()) {
            validPphList.average().toFloat()
        } else {
            36.0f // Baseline typical reading speed
        }

        val totalTrackedSessions = sessions.size
        val preferredSlotEntry = slotCounts.maxByOrNull { it.value }
        val preferredSlot = if (preferredSlotEntry != null && preferredSlotEntry.value > 0) {
            preferredSlotEntry.key
        } else {
            TimeOfDaySlot.NIGHT
        }

        val slotPercentage = if (totalTrackedSessions > 0) {
            ((slotCounts[preferredSlot] ?: 0) * 100) / totalTrackedSessions
        } else {
            75
        }

        val remainingHours = if (activeBook != null && activeBook.totalUnits > activeBook.currentPosition && avgPagesPerHour > 0) {
            (activeBook.totalUnits - activeBook.currentPosition).toFloat() / avgPagesPerHour
        } else {
            null
        }

        val rhythmInsights = ReadingRhythmInsights(
            averagePagesPerHour = (Math.round(avgPagesPerHour * 10f) / 10f),
            totalPagesRead = totalPages,
            preferredTimeSlot = preferredSlot,
            timeSlotPercentage = slotPercentage,
            estimatedRemainingHoursForActiveBook = remainingHours?.let { Math.round(it * 10f) / 10f }
        )

        return ReadingAnalytics(
            totalDaysWithReading = totalValidDays,
            totalHoursRead = (Math.round(totalHours * 10f) / 10f),
            totalMinutesRead = totalMinutes,
            consistencyPercentage = consistencyPct,
            heatmapContributions = contributions,
            weeklyDistribution = weeklyDistribution,
            rhythmInsights = rhythmInsights
        )
    }
}
