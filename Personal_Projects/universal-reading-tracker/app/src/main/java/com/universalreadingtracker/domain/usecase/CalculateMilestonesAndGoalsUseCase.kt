package com.universalreadingtracker.domain.usecase

import com.universalreadingtracker.domain.model.*
import java.time.DayOfWeek
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.format.TextStyle
import java.util.Locale

/**
 * Calculates current progress against user-configured yearly and monthly goals,
 * as well as evaluating Obsidian milestone badges.
 * Implements Opción 5 (Gamificación Elegante y Metas Configurables).
 */
class CalculateMilestonesAndGoalsUseCase {

    operator fun invoke(
        yearlyBookGoal: Int,
        monthlyMinuteGoal: Int,
        allBooks: List<Book>,
        allDailySummaries: List<DailyReadingSummary>,
        todaySummary: DailyReadingSummary?,
        allSessions: List<ReadingSession>,
        streakInfo: StreakInfo,
        now: LocalDate = LocalDate.now()
    ): Pair<ReadingGoals, List<ReadingMilestone>> {
        val currentYear = now.year
        val currentMonthValue = now.monthValue
        val currentYearMonthPrefix = String.format(Locale.ROOT, "%04d-%02d", currentYear, currentMonthValue)
        val esLocale = Locale.forLanguageTag("es-ES")
        val monthDisplayName = now.month.getDisplayName(TextStyle.FULL, esLocale)
            .replaceFirstChar { if (it.isLowerCase()) it.titlecase(esLocale) else it.toString() }

        // 1. Calculate Completed Books This Year
        val completedBooksCount = allBooks.count { book ->
            book.totalUnits > 0 && book.currentPosition >= book.totalUnits
        }

        // 2. Calculate Minutes Read in Current Month
        // Merge allDailySummaries with todaySummary to ensure today's reading is accurately included
        val monthMinutesMap = mutableMapOf<String, Int>()
        for (summary in allDailySummaries) {
            if (summary.date.startsWith(currentYearMonthPrefix)) {
                monthMinutesMap[summary.date] = summary.totalMinutesRead
            }
        }
        if (todaySummary != null && todaySummary.date.startsWith(currentYearMonthPrefix)) {
            monthMinutesMap[todaySummary.date] = maxOf(
                monthMinutesMap[todaySummary.date] ?: 0,
                todaySummary.totalMinutesRead
            )
        }
        val totalMinutesThisMonth = monthMinutesMap.values.sum()

        val goals = ReadingGoals(
            yearlyBookGoal = yearlyBookGoal,
            completedBooksThisYear = completedBooksCount,
            monthlyMinuteGoal = monthlyMinuteGoal,
            minutesReadThisMonth = totalMinutesThisMonth,
            currentYear = currentYear,
            currentMonthName = monthDisplayName
        )

        // 3. Evaluate Milestones

        // Milestone 1: Centenario de Lectura (100+ días de racha continua)
        val highestStreak = maxOf(
            streakInfo.currentStreakDays,
            streakInfo.longestStreakDays,
            allDailySummaries.count { it.isValidStreakDay }
        )
        val isCentenaryUnlocked = highestStreak >= 100
        val m1 = ReadingMilestone(
            id = "centenary_reader",
            title = "Centenario de Lectura",
            description = "Alcanzar 100 o más días de racha continua de lectura activa sin interrupción.",
            iconEmoji = "👑",
            isUnlocked = isCentenaryUnlocked,
            progressLabel = if (isCentenaryUnlocked) "$highestStreak días alcanzados" else "$highestStreak / 100 días",
            progressPercent = (highestStreak / 100f).coerceIn(0f, 1f),
            tierName = "Obsidian Gold"
        )

        // Milestone 2: Lector Bimodal (combinar Audible y Kindle en el mismo día)
        var bimodalCount = allDailySummaries.count { it.audioMinutes > 0 && it.kindleMinutes > 0 }
        if (todaySummary != null && todaySummary.audioMinutes > 0 && todaySummary.kindleMinutes > 0) {
            if (allDailySummaries.none { it.date == todaySummary.date && it.audioMinutes > 0 && it.kindleMinutes > 0 }) {
                bimodalCount += 1
            }
        }
        val isBimodalUnlocked = bimodalCount > 0
        val m2 = ReadingMilestone(
            id = "bimodal_reader",
            title = "Lector Bimodal",
            description = "Combinar lectura en Kindle y escucha en Audible en el transcurso de un mismo día.",
            iconEmoji = "⚡",
            isUnlocked = isBimodalUnlocked,
            progressLabel = if (isBimodalUnlocked) "$bimodalCount día(s) bimodales" else "0 / 1 día completado",
            progressPercent = if (isBimodalUnlocked) 1f else 0f,
            tierName = "Obsidian Amber"
        )

        // Milestone 3: Lector Nocturno (completar sesiones después de las 21:00)
        var nightSessionCount = 0
        for (session in allSessions) {
            val ts = if (session.endTime > 0) session.endTime else session.startTime
            if (ts > 0) {
                val hour = Instant.ofEpochMilli(ts).atZone(ZoneId.systemDefault()).hour
                if (hour >= 21 || hour < 5) {
                    nightSessionCount += 1
                }
            }
        }
        val isNightUnlocked = nightSessionCount > 0
        val m3 = ReadingMilestone(
            id = "night_reader",
            title = "Lector Nocturno",
            description = "Completar sesiones de lectura profunda o escucha después de las 21:00 horas.",
            iconEmoji = "🌙",
            isUnlocked = isNightUnlocked,
            progressLabel = if (isNightUnlocked) "$nightSessionCount sesión(es) nocturnas" else "0 / 1 sesión nocturna",
            progressPercent = if (isNightUnlocked) 1f else 0f,
            tierName = "Obsidian Blue"
        )

        // Milestone 4: Maratón de Fin de Semana (más de 60 min leídos en sábado o domingo)
        var maxWeekendMins = 0
        for (summary in allDailySummaries) {
            try {
                val parsedDate = LocalDate.parse(summary.date)
                if (parsedDate.dayOfWeek == DayOfWeek.SATURDAY || parsedDate.dayOfWeek == DayOfWeek.SUNDAY) {
                    if (summary.totalMinutesRead > maxWeekendMins) {
                        maxWeekendMins = summary.totalMinutesRead
                    }
                }
            } catch (_: Exception) {}
        }
        if (todaySummary != null) {
            try {
                val parsedDate = LocalDate.parse(todaySummary.date)
                if (parsedDate.dayOfWeek == DayOfWeek.SATURDAY || parsedDate.dayOfWeek == DayOfWeek.SUNDAY) {
                    if (todaySummary.totalMinutesRead > maxWeekendMins) {
                        maxWeekendMins = todaySummary.totalMinutesRead
                    }
                }
            } catch (_: Exception) {}
        }
        val isWeekendMarathonUnlocked = maxWeekendMins >= 60
        val m4 = ReadingMilestone(
            id = "weekend_marathon",
            title = "Maratón de Finde",
            description = "Superar los 60 minutos de lectura en una sola jornada de sábado o domingo.",
            iconEmoji = "☕",
            isUnlocked = isWeekendMarathonUnlocked,
            progressLabel = if (isWeekendMarathonUnlocked) "Superado ($maxWeekendMins min)" else "$maxWeekendMins / 60 min",
            progressPercent = (maxWeekendMins / 60f).coerceIn(0f, 1f),
            tierName = "Obsidian Emerald"
        )

        return Pair(goals, listOf(m1, m2, m3, m4))
    }
}
