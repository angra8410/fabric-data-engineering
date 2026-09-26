package com.universalreadingtracker.domain.usecase

import com.universalreadingtracker.domain.model.DailyReadingSummary
import com.universalreadingtracker.domain.repository.StreakRepository
import java.time.LocalDate
import java.time.format.DateTimeFormatter

/**
 * Implements RF-08 and ADR-009 from spec.md & decisions.md:
 * Seeds the pre-existing 163 consecutive days of reading into Room DB.
 * Allows the user's hard-earned streak of 163 days to be preserved and continue organically to 164.
 */
class BackfillHistoricalStreakUseCase(
    private val streakRepository: StreakRepository
) {
    suspend operator fun invoke(
        streakDays: Int = 163,
        referenceDate: LocalDate = LocalDate.now()
    ) {
        val referenceDateString = referenceDate.format(DateTimeFormatter.ISO_LOCAL_DATE)
        streakRepository.backfillHistoricalStreak(streakDays, referenceDateString)
    }
}
