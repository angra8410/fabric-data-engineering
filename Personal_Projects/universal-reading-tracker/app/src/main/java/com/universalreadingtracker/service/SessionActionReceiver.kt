package com.universalreadingtracker.service

import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.universalreadingtracker.data.local.AppDatabase
import com.universalreadingtracker.data.repository.BookRepositoryImpl
import com.universalreadingtracker.data.repository.ReadingSessionRepositoryImpl
import com.universalreadingtracker.domain.model.ReadingModality
import com.universalreadingtracker.domain.model.ReadingSession
import com.universalreadingtracker.domain.model.SessionStatus
import com.universalreadingtracker.domain.usecase.SplitMidnightSessionUseCase
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * Handles quick actions from notifications (Terminar Sesión / Continuar).
 * Implements RF-02, RF-10, ADR-004 and ADR-010 from spec.md & decisions.md.
 */
class SessionActionReceiver : BroadcastReceiver() {

    private val splitMidnightUseCase = SplitMidnightSessionUseCase()

    override fun onReceive(context: Context, intent: Intent) {
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        when (intent.action) {
            AudibleNotificationListenerService.ACTION_FINISH_SESSION -> {
                val title = intent.getStringExtra(AudibleNotificationListenerService.EXTRA_TITLE) ?: "Audiolibro"
                val author = intent.getStringExtra(AudibleNotificationListenerService.EXTRA_AUTHOR) ?: "Audible"
                val realSeconds = intent.getLongExtra(AudibleNotificationListenerService.EXTRA_SECONDS, 0L)
                val startEpoch = intent.getLongExtra(AudibleNotificationListenerService.EXTRA_START_EPOCH, System.currentTimeMillis() - (realSeconds * 1000))
                val endEpoch = System.currentTimeMillis()

                notificationManager.cancel(AudibleNotificationListenerService.NOTIFICATION_PAUSE_ID)

                if (realSeconds >= 60) {
                    val db = AppDatabase.getInstance(context)
                    val bookRepo = BookRepositoryImpl(db.bookDao())
                    val sessionRepo = ReadingSessionRepositoryImpl(db.readingSessionDao(), db.dailyReadingSummaryDao())

                    CoroutineScope(Dispatchers.IO).launch {
                        val book = bookRepo.findOrCreateBook(title, author, "audible")
                        val rawSession = ReadingSession(
                            bookId = book.id,
                            bookTitle = book.title,
                            bookAuthor = book.author,
                            modality = ReadingModality.AUDIOBOOK,
                            providerId = "audible",
                            startTime = startEpoch,
                            endTime = endEpoch,
                            realDurationSeconds = realSeconds,
                            status = SessionStatus.CONFIRMED
                        )

                        // Implements RF-10 & ADR-010: Proportional split at midnight
                        val splitSessions = splitMidnightUseCase(rawSession)
                        for (s in splitSessions) {
                            sessionRepo.insertSession(s)
                            bookRepo.updateBookProgress(book.id, null, s.realDurationSeconds)
                        }
                    }
                }
            }
            AudibleNotificationListenerService.ACTION_CONTINUE_SESSION -> {
                notificationManager.cancel(AudibleNotificationListenerService.NOTIFICATION_PAUSE_ID)
            }
        }
    }
}
