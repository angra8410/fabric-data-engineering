package com.universalreadingtracker.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.universalreadingtracker.data.local.AppDatabase
import com.universalreadingtracker.data.repository.BookRepositoryImpl
import com.universalreadingtracker.data.repository.ReadingSessionRepositoryImpl
import com.universalreadingtracker.domain.model.ReadingModality
import com.universalreadingtracker.domain.model.ReadingSession
import com.universalreadingtracker.domain.model.SessionStatus
import com.universalreadingtracker.domain.usecase.SplitMidnightSessionUseCase
import com.universalreadingtracker.presentation.MainActivity
import com.universalreadingtracker.presentation.widget.ReadingAppWidgetProvider
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/**
 * Implements RF-03, RF-04, ADR-007 and ADR-008 from spec.md & decisions.md:
 * Foreground timer service that accurately counts reading minutes while the user reads on their physical Kindle device.
 * Operates efficiently in the background with the Android phone screen off.
 */
class KindleReadingTimerService : Service() {

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var timerJob: Job? = null
    private val splitMidnightUseCase = SplitMidnightSessionUseCase()

    private var startEpoch: Long = 0L
    private var bookTitle: String = "Kindle Paperwhite / E-Reader"
    private var bookAuthor: String = "Lectura en Kindle"
    private var startPage: Int? = null

    private val notificationManager by lazy {
        getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> {
                val now = System.currentTimeMillis()
                startEpoch = now
                isRunning = true
                bookTitle = intent.getStringExtra(EXTRA_BOOK_TITLE) ?: "Libro en Kindle"
                bookAuthor = intent.getStringExtra(EXTRA_BOOK_AUTHOR) ?: "Autor"
                startPage = intent.getIntExtra(EXTRA_START_PAGE, -1).takeIf { it >= 0 }

                // Persist state to SharedPreferences to prevent loss during Android Doze or process restarts
                val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                prefs.edit()
                    .putLong(KEY_START_EPOCH, startEpoch)
                    .putString(KEY_BOOK_TITLE, bookTitle)
                    .putString(KEY_BOOK_AUTHOR, bookAuthor)
                    .putInt(KEY_START_PAGE, startPage ?: -1)
                    .putBoolean(KEY_IS_RUNNING, true)
                    .apply()

                startForeground(NOTIFICATION_ID, buildOngoingNotification(startEpoch, bookTitle))
                ReadingAppWidgetProvider.updateAllWidgets(this@KindleReadingTimerService)
                startTimer()
            }
            ACTION_STOP -> {
                isRunning = false
                ReadingAppWidgetProvider.updateAllWidgets(this@KindleReadingTimerService)
                val endPage = intent.getIntExtra(EXTRA_END_PAGE, -1).takeIf { it >= 0 }
                stopTimerAndSaveSession(endPage)
            }
        }
        return START_NOT_STICKY
    }

    private fun startTimer() {
        timerJob?.cancel()
        timerJob = serviceScope.launch {
            while (isActive) {
                delay(15000) // Update every 15 seconds to save battery; chronometer ticks natively at hardware level
                val currentMinutes = maxOf(0L, (System.currentTimeMillis() - startEpoch) / 60000L).toInt()
                notificationManager.notify(NOTIFICATION_ID, buildOngoingNotification(startEpoch, bookTitle, currentMinutes))
            }
        }
    }

    private fun stopTimerAndSaveSession(endPage: Int?) {
        timerJob?.cancel()
        val endEpoch = System.currentTimeMillis()

        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val savedStart = prefs.getLong(KEY_START_EPOCH, 0L)
        val effectiveStartEpoch = if (startEpoch > 0L) startEpoch else if (savedStart > 0L) savedStart else (endEpoch - 60000L)
        val finalTitle = prefs.getString(KEY_BOOK_TITLE, bookTitle) ?: bookTitle
        val finalAuthor = prefs.getString(KEY_BOOK_AUTHOR, bookAuthor) ?: bookAuthor
        val finalStartPage = prefs.getInt(KEY_START_PAGE, -1).takeIf { it >= 0 } ?: startPage

        // Clear persisted timer state
        prefs.edit().clear().apply()
        isRunning = false

        // Inviolable Wall-Clock Duration: immune to coroutine freezing during CPU Doze/Deep-Sleep
        val totalSeconds = maxOf(0L, (endEpoch - effectiveStartEpoch) / 1000L)

        if (totalSeconds >= 60L) {
            val db = AppDatabase.getInstance(this)
            val bookRepo = BookRepositoryImpl(db.bookDao())
            val sessionRepo = ReadingSessionRepositoryImpl(db.readingSessionDao(), db.dailyReadingSummaryDao())

            serviceScope.launch {
                val book = bookRepo.findOrCreateBook(finalTitle, finalAuthor, "kindle_physical")
                val rawSession = ReadingSession(
                    bookId = book.id,
                    bookTitle = book.title,
                    bookAuthor = book.author,
                    modality = ReadingModality.EBOOK_KINDLE,
                    providerId = "kindle_physical",
                    startTime = effectiveStartEpoch,
                    endTime = endEpoch,
                    realDurationSeconds = totalSeconds,
                    startPage = finalStartPage,
                    endPage = endPage,
                    status = SessionStatus.CONFIRMED
                )

                // Implements RF-10 & ADR-010: Midnight Splitting
                val splitSessions = splitMidnightUseCase(rawSession)
                for (s in splitSessions) {
                    sessionRepo.insertSession(s)
                    bookRepo.updateBookProgress(book.id, endPage, s.realDurationSeconds)
                }
                ReadingAppWidgetProvider.updateAllWidgets(this@KindleReadingTimerService)
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
            }
        } else {
            ReadingAppWidgetProvider.updateAllWidgets(this@KindleReadingTimerService)
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
        }
    }

    private fun buildOngoingNotification(
        startMs: Long,
        title: String,
        accumulatedMinutes: Int = 0
    ): android.app.Notification {
        val openAppIntent = Intent(this, MainActivity::class.java)
        val openPendingIntent = PendingIntent.getActivity(
            this, 201, openAppIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val stopIntent = Intent(this, KindleReadingTimerService::class.java).apply {
            action = ACTION_STOP
        }
        val stopPendingIntent = PendingIntent.getService(
            this, 202, stopIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val minutesText = if (accumulatedMinutes > 0) "$accumulatedMinutes min" else "en curso"

        return NotificationCompat.Builder(this, CHANNEL_KINDLE_TIMER)
            .setSmallIcon(android.R.drawable.ic_menu_agenda)
            .setContentTitle("Leyendo en Kindle: $title")
            .setContentText("⏱️ Cronómetro activo ($minutesText) · Toca para finalizar")
            .setUsesChronometer(true)
            .setWhen(startMs)
            .setShowWhen(true)
            .setContentIntent(openPendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .addAction(android.R.drawable.ic_menu_close_clear_cancel, "Finalizar Sesión", stopPendingIntent)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_KINDLE_TIMER,
                "Temporizador de Lectura Kindle",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Muestra el tiempo activo de lectura con el Kindle físico"
            }
            notificationManager.createNotificationChannel(channel)
        }
    }

    override fun onDestroy() {
        isRunning = false
        timerJob?.cancel()
        super.onDestroy()
    }

    companion object {
        var isRunning: Boolean = false
        private const val PREFS_NAME = "kindle_reading_timer_prefs"
        private const val KEY_START_EPOCH = "key_start_epoch"
        private const val KEY_BOOK_TITLE = "key_book_title"
        private const val KEY_BOOK_AUTHOR = "key_book_author"
        private const val KEY_START_PAGE = "key_start_page"
        private const val KEY_IS_RUNNING = "key_is_running"

        fun isTimerActive(context: Context): Boolean {
            if (isRunning) return true
            val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            return prefs.getBoolean(KEY_IS_RUNNING, false)
        }

        const val CHANNEL_KINDLE_TIMER = "kindle_reading_timer_channel"
        const val NOTIFICATION_ID = 3030
        const val ACTION_START = "com.universalreadingtracker.ACTION_START_KINDLE_TIMER"
        const val ACTION_STOP = "com.universalreadingtracker.ACTION_STOP_KINDLE_TIMER"
        const val EXTRA_BOOK_TITLE = "extra_book_title"
        const val EXTRA_BOOK_AUTHOR = "extra_book_author"
        const val EXTRA_START_PAGE = "extra_start_page"
        const val EXTRA_END_PAGE = "extra_end_page"
    }
}
