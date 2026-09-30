package com.universalreadingtracker.data.export

import android.content.Context
import android.content.Intent
import androidx.core.content.FileProvider
import com.universalreadingtracker.domain.model.Book
import com.universalreadingtracker.domain.model.DailyReadingSummary
import com.universalreadingtracker.domain.model.ReadingGoals
import com.universalreadingtracker.domain.model.ReadingMilestone
import com.universalreadingtracker.domain.model.ReadingSession
import com.universalreadingtracker.domain.model.StreakInfo
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.time.LocalDate
import java.time.format.DateTimeFormatter

/**
 * Utility to export all user reading tracking data into a formatted .JSON file
 * optimized for Big Data ingestion (e.g. PySpark on Microsoft Fabric / Databricks)
 * and trigger the native Android Share/Save sheet.
 */
object JsonExportHelper {

    fun generateJson(
        streakInfo: StreakInfo,
        books: List<Book>,
        sessions: List<ReadingSession>,
        dailySummaries: List<DailyReadingSummary>,
        goals: ReadingGoals? = null,
        milestones: List<ReadingMilestone> = emptyList()
    ): String {
        val root = JSONObject()

        // 1. Metadata
        val metadata = JSONObject().apply {
            put("app", "Universal Reading Tracker")
            put("version", "1.0.0")
            put("exportedAtEpoch", System.currentTimeMillis())
            put("exportDate", LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE))
            put("targetSchema", "FabricLakehouseMedallion_v1")
        }
        root.put("metadata", metadata)

        // 2. Streak Info
        val streakObj = JSONObject().apply {
            put("currentStreakDays", streakInfo.currentStreakDays)
            put("longestStreakDays", streakInfo.longestStreakDays)
            put("isStreakActiveToday", streakInfo.isStreakActiveToday)
            put("totalHistoricalDays", streakInfo.totalHistoricalDays)
        }
        root.put("streak", streakObj)

        // 3. Configurable Goals
        if (goals != null) {
            val goalsObj = JSONObject().apply {
                put("yearlyBookGoal", goals.yearlyBookGoal)
                put("completedBooksThisYear", goals.completedBooksThisYear)
                put("yearlyProgressPercent", goals.yearlyProgressPercent)
                put("monthlyMinuteGoal", goals.monthlyMinuteGoal)
                put("minutesReadThisMonth", goals.minutesReadThisMonth)
                put("monthlyProgressPercent", goals.monthlyProgressPercent)
                put("currentYear", goals.currentYear)
                put("currentMonthName", goals.currentMonthName)
            }
            root.put("goals", goalsObj)
        }

        // 4. Obsidian Milestones
        if (milestones.isNotEmpty()) {
            val milestonesArray = JSONArray()
            milestones.forEach { m ->
                val mObj = JSONObject().apply {
                    put("id", m.id)
                    put("title", m.title)
                    put("description", m.description)
                    put("iconEmoji", m.iconEmoji)
                    put("isUnlocked", m.isUnlocked)
                    put("progressLabel", m.progressLabel)
                    put("progressPercent", m.progressPercent)
                    put("tierName", m.tierName)
                }
                milestonesArray.put(mObj)
            }
            root.put("milestones", milestonesArray)
        }

        // 5. Books Catalog
        val booksArray = JSONArray()
        books.forEach { book ->
            val b = JSONObject().apply {
                put("id", book.id)
                put("title", book.title)
                put("author", book.author)
                put("format", book.format.name)
                put("primaryProvider", book.primaryProviderId)
                put("progressUnit", book.progressUnit.name)
                put("currentPosition", book.currentPosition)
                put("totalUnits", book.totalUnits)
                put("progressPercentage", book.progressPercentage)
                put("isCurrentlyReading", book.isCurrentlyReading)
                put("isCompleted", book.totalUnits > 0 && book.currentPosition >= book.totalUnits)
            }
            booksArray.put(b)
        }
        root.put("books", booksArray)

        // 6. Complete Reading Sessions History
        val sessionsArray = JSONArray()
        sessions.forEach { s ->
            val sess = JSONObject().apply {
                put("id", s.id)
                put("bookId", s.bookId)
                put("bookTitle", s.bookTitle)
                put("bookAuthor", s.bookAuthor)
                put("modality", s.modality.name)
                put("providerId", s.providerId)
                put("startTimeEpoch", s.startTime)
                put("endTimeEpoch", s.endTime)
                put("durationMinutes", s.durationMinutes)
                put("realDurationSeconds", s.realDurationSeconds)
                put("startPage", s.startPage)
                put("endPage", s.endPage)
                put("pagesRead", s.pagesRead ?: 0)
                put("status", s.status.name)
                put("notes", s.notes ?: "")
            }
            sessionsArray.put(sess)
        }
        root.put("sessions", sessionsArray)

        // 7. Daily Aggregated Summaries
        val summariesArray = JSONArray()
        dailySummaries.forEach { sum ->
            val d = JSONObject().apply {
                put("date", sum.date)
                put("totalMinutesRead", sum.totalMinutesRead)
                put("audioMinutes", sum.audioMinutes)
                put("kindleMinutes", sum.kindleMinutes)
                put("physicalMinutes", sum.physicalMinutes)
                put("goalReached", sum.goalReached)
                put("isHistoricalBackfill", sum.isHistoricalBackfill)
                put("isBimodal", sum.audioMinutes > 0 && sum.kindleMinutes > 0)
            }
            summariesArray.put(d)
        }
        root.put("dailySummaries", summariesArray)

        return root.toString(2)
    }

    fun shareJsonExport(
        context: Context,
        streakInfo: StreakInfo,
        books: List<Book>,
        sessions: List<ReadingSession>,
        dailySummaries: List<DailyReadingSummary>,
        goals: ReadingGoals? = null,
        milestones: List<ReadingMilestone> = emptyList()
    ): File {
        val jsonContent = generateJson(streakInfo, books, sessions, dailySummaries, goals, milestones)
        val todayStr = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE)
        val fileName = "universal_reading_tracker_export_$todayStr.json"

        val exportFile = File(context.cacheDir, fileName)
        exportFile.writeText(jsonContent, Charsets.UTF_8)

        val fileUri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            exportFile
        )

        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "application/json"
            putExtra(Intent.EXTRA_STREAM, fileUri)
            putExtra(Intent.EXTRA_SUBJECT, "Universal Reading Tracker Export ($todayStr)")
            putExtra(Intent.EXTRA_TEXT, "Exportación completa en JSON para ingesta en PySpark / Microsoft Fabric Lakehouse ($todayStr).")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }

        val chooser = Intent.createChooser(intent, "Exportar datos a Fabric / Drive")
        chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(chooser)

        return exportFile
    }
}
