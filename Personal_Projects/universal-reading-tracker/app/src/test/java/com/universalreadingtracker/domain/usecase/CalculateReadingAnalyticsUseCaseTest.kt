package com.universalreadingtracker.domain.usecase

import com.universalreadingtracker.domain.model.Book
import com.universalreadingtracker.domain.model.BookFormat
import com.universalreadingtracker.domain.model.DailyReadingSummary
import com.universalreadingtracker.domain.model.ProgressUnit
import com.universalreadingtracker.domain.model.ReadingModality
import com.universalreadingtracker.domain.model.ReadingSession
import com.universalreadingtracker.domain.model.SessionStatus
import com.universalreadingtracker.domain.model.TimeOfDaySlot
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDate
import java.time.ZoneId

class CalculateReadingAnalyticsUseCaseTest {

    private val useCase = CalculateReadingAnalyticsUseCase()

    @Test
    fun `test calculates correct heatmap contributions and total hours`() {
        val summaries = listOf(
            DailyReadingSummary("2026-09-28", 30, 15, 15, 0, true),
            DailyReadingSummary("2026-09-29", 60, 20, 40, 0, true)
        )

        val analytics = useCase(
            summaries = summaries,
            sessions = emptyList(),
            today = LocalDate.of(2026, 9, 29)
        )

        assertEquals(2, analytics.totalDaysWithReading)
        assertEquals(90, analytics.totalMinutesRead)
        assertEquals(1.5f, analytics.totalHoursRead, 0.01f)

        val day28 = analytics.heatmapContributions["2026-09-28"]
        assertNotNull(day28)
        assertEquals(2, day28?.intensityLevel) // 30 min is level 2

        val day29 = analytics.heatmapContributions["2026-09-29"]
        assertNotNull(day29)
        assertEquals(3, day29?.intensityLevel) // 60 min is level 3
    }

    @Test
    fun `test calculates reading rhythm and preferred time slot correctly`() {
        val book = Book(
            id = 1L,
            title = "Hábitos Atómicos",
            author = "James Clear",
            format = BookFormat.EBOOK,
            primaryProviderId = "kindle_physical",
            progressUnit = ProgressUnit.PAGES,
            currentPosition = 100,
            totalUnits = 200,
            isCurrentlyReading = true
        )

        // Session at 8:00 PM (20:00) -> NIGHT
        // 20 pages read in 1800 seconds (30 min) -> 40 pages/hour
        val startTime = 1790694000000L // arbitrary evening epoch
        val session = ReadingSession(
            id = 1L,
            bookId = 1L,
            bookTitle = "Hábitos Atómicos",
            bookAuthor = "James Clear",
            modality = ReadingModality.EBOOK_KINDLE,
            providerId = "kindle_physical",
            startTime = startTime,
            endTime = startTime + 1800000L,
            realDurationSeconds = 1800L,
            startPage = 80,
            endPage = 100,
            pagesRead = 20,
            status = SessionStatus.CONFIRMED
        )

        val analytics = useCase(
            summaries = emptyList(),
            sessions = listOf(session),
            activeBook = book,
            today = LocalDate.of(2026, 9, 29),
            zoneId = ZoneId.of("UTC")
        )

        assertEquals(20, analytics.rhythmInsights.totalPagesRead)
        assertEquals(40.0f, analytics.rhythmInsights.averagePagesPerHour, 0.1f)
        // 100 remaining pages at 40 pages/hr = 2.5 hours
        assertEquals(2.5f, analytics.rhythmInsights.estimatedRemainingHoursForActiveBook ?: 0f, 0.1f)
    }

    @Test
    fun `test weekly distribution computes percentages accurately`() {
        val summaries = listOf(
            DailyReadingSummary("2026-09-28", 50, 20, 30, 0, true) // Monday
        )

        val analytics = useCase(
            summaries = summaries,
            sessions = emptyList(),
            today = LocalDate.of(2026, 9, 29)
        )

        assertEquals(20, analytics.weeklyDistribution.totalAudioMinutes)
        assertEquals(30, analytics.weeklyDistribution.totalKindleMinutes)
        assertEquals(40, analytics.weeklyDistribution.audioPercentage)
        assertEquals(60, analytics.weeklyDistribution.kindlePercentage)
        assertEquals(7, analytics.weeklyDistribution.weekDays.size)
    }
}
