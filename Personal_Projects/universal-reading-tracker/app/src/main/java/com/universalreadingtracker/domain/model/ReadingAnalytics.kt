package com.universalreadingtracker.domain.model

enum class TimeOfDaySlot(val label: String, val emoji: String, val timeRange: String) {
    MORNING("Lector Matutino", "☀️", "06:00 - 12:00"),
    AFTERNOON("Lector Vespertino", "🌤️", "12:00 - 18:00"),
    NIGHT("Lector Nocturno", "🌙", "18:00 - 00:00"),
    DAWN("Lector de Madrugada", "✨", "00:00 - 06:00")
}

data class DayContribution(
    val date: String, // YYYY-MM-DD
    val totalMinutes: Int,
    val audioMinutes: Int,
    val kindleMinutes: Int,
    val physicalMinutes: Int,
    val intensityLevel: Int // 0 to 4
)

data class DayModalityItem(
    val dayLabel: String, // L, M, M, J, V, S, D
    val date: String,
    val audioMinutes: Int,
    val kindleMinutes: Int,
    val totalMinutes: Int,
    val isToday: Boolean,
    val isFuture: Boolean
)

data class WeeklyModalityDistribution(
    val weekDays: List<DayModalityItem>,
    val totalAudioMinutes: Int,
    val totalKindleMinutes: Int,
    val audioPercentage: Int,
    val kindlePercentage: Int
)

data class ReadingRhythmInsights(
    val averagePagesPerHour: Float,
    val totalPagesRead: Int,
    val preferredTimeSlot: TimeOfDaySlot,
    val timeSlotPercentage: Int,
    val estimatedRemainingHoursForActiveBook: Float?
)

data class ReadingAnalytics(
    val totalDaysWithReading: Int,
    val totalHoursRead: Float,
    val totalMinutesRead: Int,
    val consistencyPercentage: Int,
    val heatmapContributions: Map<String, DayContribution>,
    val weeklyDistribution: WeeklyModalityDistribution,
    val rhythmInsights: ReadingRhythmInsights
)
