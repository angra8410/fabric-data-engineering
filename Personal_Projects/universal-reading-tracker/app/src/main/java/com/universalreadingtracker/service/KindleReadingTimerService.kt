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
    private var elapsedSeconds: Long = 0L
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
                bookTitle = intent.getStringExtra(EXTRA_BOOK_TITLE) ?: "Libro en Kindle"
                bookAuthor = intent.getStringExtra(EXTRA_BOOK_AUTHOR) ?: "Autor"
                startPage = intent.getIntExtra(EXTRA_START_PAGE, -1).takeIf { it >= 0 }
                startEpoch = System.currentTimeMillis()
                elapsedSeconds = 0L

                startForeground(NOTIFICATION_ID, buildOngoingNotification(0))
                startTimer()
            }
            ACTION_STOP -> {
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
                delay(1000)
                elapsedSeconds++
                if (elapsedSeconds % 60 == 0L) {
                    val minutes = (elapsedSeconds / 60).toInt()
                    notificationManager.notify(NOTIFICATION_ID, buildOngoingNotification(minutes))
                }
            }
        }
    }

    private fun stopTimerAndSaveSession(endPage: Int?) {
        timerJob?.cancel()
        val endEpoch = System.currentTimeMillis()
        val totalSeconds = elapsedSeconds

        if (totalSeconds >= 60) {
            val db = AppDatabase.getInstance(this)
            val bookRepo = BookRepositoryImpl(db.bookDao())
            val sessionRepo = ReadingSessionRepositoryImpl(db.readingSessionDao(), db.dailyReadingSummaryDao())

            serviceScope.launch {
                val book = bookRepo.findOrCreateBook(bookTitle, bookAuthor, "kindle_physical")
                val rawSession = ReadingSession(
                    bookId = book.id,
                    bookTitle = book.title,
                    bookAuthor = book.author,
                    modality = ReadingModality.EBOOK_KINDLE,
                    providerId = "kindle_physical",
                    startTime = startEpoch,
                    endTime = endEpoch,
                    realDurationSeconds = totalSeconds,
                    startPage = startPage,
                    endPage = endPage,
                    status = SessionStatus.CONFIRMED
                )

                // Implements RF-10 & ADR-010: Midnight Splitting
                val splitSessions = splitMidnightUseCase(rawSession)
                for (s in splitSessions) {
                    sessionRepo.insertSession(s)
                    bookRepo.updateBookProgress(book.id, endPage, s.realDurationSeconds)
                }
                stopSelf()
            }
        } else {
            stopSelf()
        }
    }

    private fun buildOngoingNotification(minutes: Int): android.app.Notification {
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

        return NotificationCompat.Builder(this, CHANNEL_KINDLE_TIMER)
            .setSmallIcon(android.R.drawable.ic_menu_agenda)
            .setContentTitle("Leyendo en Kindle: $bookTitle")
            .setContentText("⏱️ $minutes min acumulados · Toca para finalizar")
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
        timerJob?.cancel()
        super.onDestroy()
    }

    companion object {
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
