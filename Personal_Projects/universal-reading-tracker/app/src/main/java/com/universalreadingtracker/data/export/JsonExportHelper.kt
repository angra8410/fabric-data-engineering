package com.universalreadingtracker.data.export

import android.content.Context
import android.content.Intent
import androidx.core.content.FileProvider
import com.universalreadingtracker.domain.model.Book
import com.universalreadingtracker.domain.model.DailyReadingSummary
import com.universalreadingtracker.domain.model.ReadingSession
import com.universalreadingtracker.domain.model.StreakInfo
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.time.LocalDate
import java.time.format.DateTimeFormatter

/**
 * Utility to export all user reading tracking data into a formatted .JSON file
 * and trigger the native Android Share/Save sheet.
 */
object JsonExportHelper {

    fun generateJson(
        streakInfo: StreakInfo,
        books: List<Book>,
        sessions: List<ReadingSession>,
        dailySummaries: List<DailyReadingSummary>
    ): String {
        val root = JSONObject()

        // 1. Metadata
        val metadata = JSONObject().apply {
            put("app", "Universal Reading Tracker")
            put("version", "1.0.0")
            put("exportedAt", System.currentTimeMillis())
            put("exportDate", LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE))
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

        // 3. Books Catalog
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
            }
            booksArray.put(b)
        }
        root.put("books", booksArray)

        // 4. Reading Sessions History
        val sessionsArray = JSONArray()
        sessions.forEach { s ->
            val sess = JSONObject().apply {
                put("id", s.id)
                put("bookTitle", s.bookTitle)
                put("bookAuthor", s.bookAuthor)
                put("modality", s.modality.name)
                put("providerId", s.providerId)
                put("startTime", s.startTime)
                put("endTime", s.endTime)
                put("durationMinutes", s.durationMinutes)
                put("realDurationSeconds", s.realDurationSeconds)
                put("startPage", s.startPage)
                put("endPage", s.endPage)
            }
            sessionsArray.put(sess)
        }
        root.put("sessions", sessionsArray)

        // 5. Daily Aggregated Summaries
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
            }
            summariesArray.put(d)
        }
        root.put("dailySummaries", summariesArray)

        return root.toString(2) // Indented with 2 spaces for human-readable JSON
    }

    fun shareJsonExport(
        context: Context,
        streakInfo: StreakInfo,
        books: List<Book>,
        sessions: List<ReadingSession>,
        dailySummaries: List<DailyReadingSummary>
    ): File {
        val jsonContent = generateJson(streakInfo, books, sessions, dailySummaries)
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
            putExtra(Intent.EXTRA_SUBJECT, "Backup de Universal Reading Tracker ($todayStr)")
            putExtra(Intent.EXTRA_TEXT, "Exportación de datos de lectura JSON generada el $todayStr.")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }

        val chooser = Intent.createChooser(intent, "Exportar datos en JSON")
        chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(chooser)

        return exportFile
    }
}
