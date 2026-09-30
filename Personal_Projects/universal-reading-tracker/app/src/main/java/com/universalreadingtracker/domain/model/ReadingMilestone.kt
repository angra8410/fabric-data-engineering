package com.universalreadingtracker.domain.model

/**
 * Represents an elegant Obsidian-tier milestone badge.
 * Implements Opción 5 (Gamificación Elegante y Milestones).
 */
data class ReadingMilestone(
    val id: String,
    val title: String,
    val description: String,
    val iconEmoji: String,
    val isUnlocked: Boolean,
    val progressLabel: String,
    val progressPercent: Float, // 0.0f to 1.0f
    val tierName: String = "Obsidian Gold",
    val unlockDate: String? = null
)

/**
 * Represents yearly and monthly configurable reading goals and current progress.
 */
data class ReadingGoals(
    val yearlyBookGoal: Int = 12,
    val completedBooksThisYear: Int = 0,
    val monthlyMinuteGoal: Int = 1000,
    val minutesReadThisMonth: Int = 0,
    val currentYear: Int = 2026,
    val currentMonthName: String = "Septiembre"
) {
    val yearlyProgressPercent: Float
        get() = if (yearlyBookGoal > 0) (completedBooksThisYear.toFloat() / yearlyBookGoal).coerceIn(0f, 1f) else 0f

    val monthlyProgressPercent: Float
        get() = if (monthlyMinuteGoal > 0) (minutesReadThisMonth.toFloat() / monthlyMinuteGoal).coerceIn(0f, 1f) else 0f

    val remainingBooks: Int
        get() = maxOf(0, yearlyBookGoal - completedBooksThisYear)

    val remainingMinutesThisMonth: Int
        get() = maxOf(0, monthlyMinuteGoal - minutesReadThisMonth)
}
