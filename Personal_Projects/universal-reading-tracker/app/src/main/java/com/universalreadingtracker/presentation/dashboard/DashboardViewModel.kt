package com.universalreadingtracker.presentation.dashboard

import android.app.Application
import android.content.Context
import android.content.Intent
import androidx.core.content.ContextCompat
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.universalreadingtracker.UniversalReadingApp
import com.universalreadingtracker.data.repository.BookRepositoryImpl
import com.universalreadingtracker.data.repository.ReadingSessionRepositoryImpl
import com.universalreadingtracker.data.repository.StreakRepositoryImpl
import com.universalreadingtracker.service.KindleReadingTimerService
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.format.DateTimeFormatter

/**
 * ViewModel managing the consolidated dashboard state, active streaks, and Kindle timer.
 * Implements RF-05, RF-06, RF-08 and ADR-005 from spec.md & decisions.md.
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
        observeTodaySummary()
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

    private fun observeTodaySummary() {
        viewModelScope.launch {
            val todayStr = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE)
            val summary = sessionRepo.getSummaryForDate(todayStr)
            _uiState.update { it.copy(todaySummary = summary) }
        }
    }

    fun toggleKindleReadingTimer(bookTitle: String = "Kindle Paperwhite", bookAuthor: String = "Kindle") {
        val context = getApplication<Application>()
        val isStarting = !_uiState.value.isKindleTimerRunning

        val intent = Intent(context, KindleReadingTimerService::class.java).apply {
            action = if (isStarting) KindleReadingTimerService.ACTION_START else KindleReadingTimerService.ACTION_STOP
            if (isStarting) {
                putExtra(KindleReadingTimerService.EXTRA_BOOK_TITLE, bookTitle)
                putExtra(KindleReadingTimerService.EXTRA_BOOK_AUTHOR, bookAuthor)
            }
        }

        if (isStarting) {
            ContextCompat.startForegroundService(context, intent)
        } else {
            context.startService(intent)
        }

        _uiState.update { it.copy(isKindleTimerRunning = isStarting) }
    }
}
