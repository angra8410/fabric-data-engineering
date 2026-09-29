package com.universalreadingtracker.presentation.dashboard

import android.app.Application
import android.content.Context
import android.content.Intent
import androidx.core.content.ContextCompat
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.universalreadingtracker.UniversalReadingApp
import com.universalreadingtracker.data.export.JsonExportHelper
import com.universalreadingtracker.data.repository.BookRepositoryImpl
import com.universalreadingtracker.data.repository.ReadingSessionRepositoryImpl
import com.universalreadingtracker.data.repository.StreakRepositoryImpl
import com.universalreadingtracker.domain.model.Book
import com.universalreadingtracker.domain.model.BookFormat
import com.universalreadingtracker.domain.model.ProgressUnit
import com.universalreadingtracker.domain.usecase.BackfillHistoricalStreakUseCase
import com.universalreadingtracker.service.KindleReadingTimerService
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.time.LocalDate
import java.time.format.DateTimeFormatter

/**
 * ViewModel managing the consolidated dashboard state, active streaks, Kindle timer,
 * active book selection, progress tracking (Pages / Loc), and JSON export.
 * Implements RF-05, RF-06, RF-08, ADR-005 and ADR-014.
 */
class DashboardViewModel(application: Application) : AndroidViewModel(application) {

    private val db = (application as UniversalReadingApp).database
    private val bookRepo = BookRepositoryImpl(db.bookDao())
    private val sessionRepo = ReadingSessionRepositoryImpl(db.readingSessionDao(), db.dailyReadingSummaryDao())
    private val streakRepo = StreakRepositoryImpl(db.dailyReadingSummaryDao())

    private val _uiState = MutableStateFlow(DashboardState())
    val uiState: StateFlow<DashboardState> = _uiState.asStateFlow()

    init {
        observeStreakInfo()
        observeRecentSessions()
        observeActiveBooks()
        observeActiveBook()
        observeTodaySummary()
        observeAllDailySummaries()
        syncTimerState()
        syncEnrichedCatalogFromAssets()
    }

    fun syncTimerState() {
        _uiState.update { it.copy(isKindleTimerRunning = KindleReadingTimerService.isRunning) }
    }

    fun syncEnrichedCatalogFromAssets() {
        viewModelScope.launch {
            try {
                val assetManager = getApplication<Application>().assets
                val jsonString = assetManager.open("books_catalog.json").bufferedReader().use { it.readText() }
                importCatalogFromJson(jsonString)
            } catch (e: Exception) {
                ensureInitialBookSeedFallback()
            }
        }
    }

    fun importCatalogJson(jsonContent: String) {
        viewModelScope.launch {
            importCatalogFromJson(jsonContent)
        }
    }

    private suspend fun importCatalogFromJson(jsonString: String) {
        try {
            val jsonArray = if (jsonString.trim().startsWith("[")) {
                JSONArray(jsonString)
            } else {
                val rootObj = JSONObject(jsonString)
                rootObj.optJSONArray("books") ?: JSONArray()
            }

            var firstInsertedId: Long? = null

            for (i in 0 until jsonArray.length()) {
                val obj = jsonArray.getJSONObject(i)
                val title = obj.optString("title", "").trim()
                if (title.isBlank()) continue
                val author = obj.optString("author", "Autor Desconocido").trim()
                val totalUnits = obj.optInt("totalUnits", obj.optInt("pageCount", 320))
                val unitStr = obj.optString("progressUnit", "PAGES")
                val unit = if (unitStr.equals("LOCATIONS", ignoreCase = true)) ProgressUnit.LOCATIONS else ProgressUnit.PAGES
                val curPos = obj.optInt("currentPosition", 0)

                val existing = bookRepo.findByTitleAndAuthor(title, author)
                if (existing == null) {
                    val newBook = Book(
                        title = title,
                        author = author,
                        format = BookFormat.EBOOK,
                        primaryProviderId = "kindle_physical",
                        progressUnit = unit,
                        currentPosition = curPos,
                        totalUnits = if (totalUnits > 0) totalUnits else 320,
                        isCurrentlyReading = false
                    )
                    val insertedId = bookRepo.insertOrUpdateBook(newBook)
                    if (firstInsertedId == null) firstInsertedId = insertedId
                }
            }

            val active = bookRepo.getActiveReadingBookSync()
            if (active == null) {
                if (firstInsertedId != null) {
                    bookRepo.setActiveReadingBook(firstInsertedId)
                } else {
                    ensureInitialBookSeedFallback()
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
            ensureInitialBookSeedFallback()
        }
    }

    private suspend fun ensureInitialBookSeedFallback() {
        val active = bookRepo.getActiveReadingBookSync()
        if (active == null) {
            val seedBook = Book(
                title = "Hábitos Atómicos",
                author = "James Clear",
                format = BookFormat.EBOOK,
                primaryProviderId = "kindle_physical",
                progressUnit = ProgressUnit.PAGES,
                currentPosition = 145,
                totalUnits = 320,
                isCurrentlyReading = true
            )
            val id = bookRepo.insertOrUpdateBook(seedBook)
            bookRepo.setActiveReadingBook(id)
        }
    }

    private fun observeStreakInfo() {
        viewModelScope.launch {
            streakRepo.getStreakInfo().collectLatest { streakInfo ->
                _uiState.update { it.copy(streakInfo = streakInfo) }
            }
        }
    }

    private fun observeRecentSessions() {
        viewModelScope.launch {
            sessionRepo.getAllSessions().collectLatest { sessions ->
                _uiState.update { it.copy(recentSessions = sessions.take(15)) }
            }
        }
    }

    private fun observeActiveBooks() {
        viewModelScope.launch {
            bookRepo.getAllBooks().collectLatest { books ->
                _uiState.update { it.copy(activeBooks = books) }
            }
        }
    }

    private fun observeActiveBook() {
        viewModelScope.launch {
            bookRepo.getActiveReadingBook().collectLatest { activeBook ->
                _uiState.update { it.copy(activeBook = activeBook) }
            }
        }
    }

    private fun observeTodaySummary() {
        viewModelScope.launch {
            val todayStr = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE)
            // Ensure no legacy dummy backfill remains on today
            db.dailyReadingSummaryDao().deleteHistoricalBackfillForDate(todayStr)

            // Self-healing check (ADR-015): ensure yesterday and full 164-day streak are preserved
            if (!streakRepo.hasCompletedBackfill()) {
                val backfillUseCase = BackfillHistoricalStreakUseCase(streakRepo)
                backfillUseCase(streakDays = 164, referenceDate = LocalDate.now())
            }

            sessionRepo.observeSummaryForDate(todayStr).collectLatest { summary ->
                _uiState.update { it.copy(todaySummary = summary) }
            }
        }
    }

    private fun observeAllDailySummaries() {
        viewModelScope.launch {
            sessionRepo.getDailySummaries(limitDays = 730).collectLatest { summaries ->
                _uiState.update { it.copy(allDailySummaries = summaries) }
            }
        }
    }

    fun selectActiveBook(bookId: Long) {
        viewModelScope.launch {
            bookRepo.setActiveReadingBook(bookId)
        }
    }

    fun addNewBook(
        title: String,
        author: String,
        unit: ProgressUnit,
        currentPos: Int,
        totalUnits: Int
    ) {
        viewModelScope.launch {
            val newBook = Book(
                title = title.trim(),
                author = author.trim().ifBlank { "Kindle Físico" },
                format = BookFormat.EBOOK,
                primaryProviderId = "kindle_physical",
                progressUnit = unit,
                currentPosition = currentPos,
                totalUnits = totalUnits,
                isCurrentlyReading = true
            )
            val id = bookRepo.insertOrUpdateBook(newBook)
            bookRepo.setActiveReadingBook(id)
        }
    }

    fun updateActiveBookPosition(newPosition: Int) {
        val currentBook = _uiState.value.activeBook ?: return
        viewModelScope.launch {
            bookRepo.updateBookPosition(currentBook.id, newPosition)
        }
    }

    fun toggleKindleReadingTimer() {
        val context = getApplication<Application>()
        val isStarting = !KindleReadingTimerService.isRunning
        val currentBook = _uiState.value.activeBook
        val title = currentBook?.title ?: "Kindle Paperwhite"
        val author = currentBook?.author ?: "Kindle Físico"

        val intent = Intent(context, KindleReadingTimerService::class.java).apply {
            action = if (isStarting) KindleReadingTimerService.ACTION_START else KindleReadingTimerService.ACTION_STOP
            if (isStarting) {
                putExtra(KindleReadingTimerService.EXTRA_BOOK_TITLE, title)
                putExtra(KindleReadingTimerService.EXTRA_BOOK_AUTHOR, author)
            }
        }

        if (isStarting) {
            ContextCompat.startForegroundService(context, intent)
        } else {
            context.startService(intent)
        }

        _uiState.update { it.copy(isKindleTimerRunning = isStarting) }
    }

    fun exportDataToJson(context: Context): File {
        val s = _uiState.value
        return JsonExportHelper.shareJsonExport(
            context = context,
            streakInfo = s.streakInfo,
            books = s.activeBooks,
            sessions = s.recentSessions,
            dailySummaries = s.allDailySummaries
        )
    }
}
