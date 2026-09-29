package com.universalreadingtracker.domain.usecase

import com.universalreadingtracker.domain.model.DailyReadingSummary
import com.universalreadingtracker.domain.repository.StreakRepository
import java.time.LocalDate
import java.time.format.DateTimeFormatter

/**
 * Implements RF-08, ADR-009 and ADR-015 from spec.md & decisions.md:
 * Seeds the pre-existing 164 consecutive days of reading into Room DB.
 * Allows the user's hard-earned streak of 164 days to be preserved and continue organically to 165.
 */
class BackfillHistoricalStreakUseCase(
    private val streakRepository: StreakRepository
) {
    suspend operator fun invoke(
        streakDays: Int = 164,
        referenceDate: LocalDate = LocalDate.now()
    ) {
        val referenceDateString = referenceDate.format(DateTimeFormatter.ISO_LOCAL_DATE)
        streakRepository.backfillHistoricalStreak(streakDays, referenceDateString)
    }
}
