package com.universalreadingtracker.domain.model

/**
 * Domain entity representing the aggregated reading progress for a calendar day.
 * Implements Section 3 and RF-08 / RF-09 from spec.md.
 */
data class DailyReadingSummary(
    val date: String, // ISO format: YYYY-MM-DD
    val totalMinutesRead: Int,
    val audioMinutes: Int,
    val kindleMinutes: Int,
    val physicalMinutes: Int,
    val goalReached: Boolean,
    val isHistoricalBackfill: Boolean = false // Implements ADR-009 (163 days backfill)
) {
    /**
     * Implements RF-09: A day counts for streak maintenance if at least 1 minute of valid reading occurred.
     */
    val isValidStreakDay: Boolean
        get() = totalMinutesRead >= 1 || isHistoricalBackfill
}

/**
 * Represents the current streak state of the user.
 */
data class StreakInfo(
    val currentStreakDays: Int,
    val longestStreakDays: Int,
    val isStreakActiveToday: Boolean,
    val totalHistoricalDays: Int
)
