package com.universalreadingtracker.domain.usecase

import com.universalreadingtracker.domain.model.ReadingModality
import com.universalreadingtracker.domain.model.ReadingSession
import org.junit.Assert.assertEquals
import org.junit.Test
import java.time.LocalDate
import java.time.ZoneId

/**
 * Unit tests verifying RF-10 and ADR-010: Midnight Splitting.
 */
class SplitMidnightSessionUseCaseTest {

    private val useCase = SplitMidnightSessionUseCase()
    private val zoneId = ZoneId.of("UTC")

    @Test
    fun sessionWithinSameDay_doesNotSplit() {
        val date = LocalDate.of(2026, 9, 26)
        val start = date.atTime(14, 0).atZone(zoneId).toInstant().toEpochMilli()
        val end = date.atTime(14, 30).atZone(zoneId).toInstant().toEpochMilli()

        val session = ReadingSession(
            id = 1,
            bookId = 1,
            modality = ReadingModality.AUDIOBOOK,
            providerId = "audible",
            startTime = start,
            endTime = end,
            realDurationSeconds = 1800 // 30 mins
        )

        val result = useCase(session, zoneId)
        assertEquals(1, result.size)
        assertEquals(1800L, result[0].realDurationSeconds)
    }

    @Test
    fun sessionCrossingMidnight_splitsProportionally() {
        val day1 = LocalDate.of(2026, 9, 26)
        val day2 = LocalDate.of(2026, 9, 27)

        // 23:45 to 00:15 (30 min total: 15 min on day 1, 15 min on day 2)
        val start = day1.atTime(23, 45).atZone(zoneId).toInstant().toEpochMilli()
        val end = day2.atTime(0, 15).atZone(zoneId).toInstant().toEpochMilli()

        val session = ReadingSession(
            id = 1,
            bookId = 1,
            modality = ReadingModality.EBOOK_KINDLE,
            providerId = "kindle_physical",
            startTime = start,
            endTime = end,
            realDurationSeconds = 1800 // 30 mins
        )

        val result = useCase(session, zoneId)
        assertEquals(2, result.size)

        // 50% before midnight, 50% after midnight
        assertEquals(900L, result[0].realDurationSeconds)
        assertEquals(900L, result[1].realDurationSeconds)
    }
}
