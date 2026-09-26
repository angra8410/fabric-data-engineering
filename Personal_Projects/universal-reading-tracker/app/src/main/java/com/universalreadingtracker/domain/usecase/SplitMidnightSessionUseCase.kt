package com.universalreadingtracker.domain.usecase

import com.universalreadingtracker.domain.model.ReadingSession
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.temporal.ChronoUnit

/**
 * Implements RF-10 and ADR-010 from spec.md & decisions.md:
 * Automatically splits reading sessions that cross the midnight boundary (00:00:00 local time)
 * into proportional segments allocated to the respective calendar days.
 */
class SplitMidnightSessionUseCase {

    operator fun invoke(session: ReadingSession, zoneId: ZoneId = ZoneId.systemDefault()): List<ReadingSession> {
        val startInstant = Instant.ofEpochMilli(session.startTime)
        val endInstant = Instant.ofEpochMilli(session.endTime)

        val startDate = startInstant.atZone(zoneId).toLocalDate()
        val endDate = endInstant.atZone(zoneId).toLocalDate()

        // If session starts and ends on the same calendar day, no split needed
        if (startDate == endDate) {
            return listOf(session)
        }

        // Calculate the exact midnight timestamp separating the two days
        val midnightInstant = endDate.atStartOfDay(zoneId).toInstant()
        val midnightEpoch = midnightInstant.toEpochMilli()

        val totalDurationMillis = maxOf(1L, session.endTime - session.startTime)
        val millisBeforeMidnight = maxOf(0L, midnightEpoch - session.startTime)
        val millisAfterMidnight = maxOf(0L, session.endTime - midnightEpoch)

        // Proportionally distribute the real wall-clock seconds
        val ratioBefore = millisBeforeMidnight.toDouble() / totalDurationMillis.toDouble()
        val secondsBefore = (session.realDurationSeconds * ratioBefore).toLong()
        val secondsAfter = maxOf(0L, session.realDurationSeconds - secondsBefore)

        val sessionBeforeMidnight = session.copy(
            id = 0,
            startTime = session.startTime,
            endTime = midnightEpoch,
            realDurationSeconds = secondsBefore,
            notes = (session.notes ?: "") + " [Día 1 de sesión trans-medianoche]"
        )

        val sessionAfterMidnight = session.copy(
            id = 0,
            startTime = midnightEpoch,
            endTime = session.endTime,
            realDurationSeconds = secondsAfter,
            notes = (session.notes ?: "") + " [Día 2 de sesión trans-medianoche]"
        )

        return listOf(sessionBeforeMidnight, sessionAfterMidnight)
    }
}
