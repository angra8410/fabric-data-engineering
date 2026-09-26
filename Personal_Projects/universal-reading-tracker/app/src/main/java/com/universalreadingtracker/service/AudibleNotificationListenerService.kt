package com.universalreadingtracker.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.media.MediaMetadata
import android.media.session.MediaController
import android.media.session.MediaSessionManager
import android.media.session.PlaybackState
import android.os.Build
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import androidx.core.app.NotificationCompat
import com.universalreadingtracker.data.local.AppDatabase
import com.universalreadingtracker.data.provider.AudibleProviderAdapter
import com.universalreadingtracker.data.repository.BookRepositoryImpl
import com.universalreadingtracker.data.repository.ReadingSessionRepositoryImpl
import com.universalreadingtracker.domain.model.ReadingModality
import com.universalreadingtracker.domain.model.ReadingSession
import com.universalreadingtracker.domain.model.SessionStatus
import com.universalreadingtracker.domain.usecase.SplitMidnightSessionUseCase
import com.universalreadingtracker.presentation.MainActivity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/**
 * Implements RF-01, RF-02, ADR-001 and ADR-004 from spec.md & decisions.md:
 * Passively listens for Audible (com.audible.application) playback events via MediaSession.
 * Accurately tracks wall-clock active listening time, freezes on pause, and displays
 * interactive notifications with [Terminar Sesión] and [Continuar] quick action buttons.
 */
class AudibleNotificationListenerService : NotificationListenerService() {

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val audibleAdapter = AudibleProviderAdapter()
    private val splitMidnightUseCase = SplitMidnightSessionUseCase()

    private var activeBookTitle: String = ""
    private var activeBookAuthor: String = ""
    private var sessionStartEpoch: Long = 0L
    private var segmentStartEpoch: Long = 0L
    private var accumulatedSeconds: Long = 0L
    private var isCurrentlyPlaying: Boolean = false

    private val notificationManager by lazy {
        getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        super.onNotificationPosted(sbn)
        if (sbn == null) return

        if (audibleAdapter.canHandle(sbn.packageName)) {
            inspectAudibleMediaSession()
        }
    }

    private fun inspectAudibleMediaSession() {
        val mediaSessionManager = getSystemService(Context.MEDIA_SESSION_SERVICE) as? MediaSessionManager ?: return

        try {
            val controllers = mediaSessionManager.getActiveSessions(
                android.content.ComponentName(this, AudibleNotificationListenerService::class.java)
            )

            val audibleController = controllers.firstOrNull { audibleAdapter.canHandle(it.packageName) }
            if (audibleController != null) {
                handleMediaControllerState(audibleController)
            }
        } catch (e: SecurityException) {
            // Permission ACTION_NOTIFICATION_LISTENER_SETTINGS must be granted by the user
        }
    }

    private fun handleMediaControllerState(controller: MediaController) {
        val state = controller.playbackState ?: return
        val metadata = controller.metadata

        val title = metadata?.getString(MediaMetadata.METADATA_KEY_TITLE) ?: "Audiolibro en Audible"
        val author = metadata?.getString(MediaMetadata.METADATA_KEY_ARTIST) ?: "Audible"

        val isPlaying = state.state == PlaybackState.STATE_PLAYING

        if (isPlaying && !isCurrentlyPlaying) {
            // Audio resumed or started
            isCurrentlyPlaying = true
            activeBookTitle = title
            activeBookAuthor = author
            val now = System.currentTimeMillis()
            if (sessionStartEpoch == 0L) {
                sessionStartEpoch = now
            }
            segmentStartEpoch = now
            dismissPauseNotification()
        } else if (!isPlaying && isCurrentlyPlaying) {
            // Audio paused -> Freeze stopwatch and show interactive notification (RF-02 & ADR-004)
            isCurrentlyPlaying = false
            val now = System.currentTimeMillis()
            val segmentDuration = (now - segmentStartEpoch) / 1000L
            accumulatedSeconds += maxOf(0L, segmentDuration)

            showInteractivePauseNotification(activeBookTitle, accumulatedSeconds)
        }
    }

    private fun showInteractivePauseNotification(bookTitle: String, secondsRead: Long) {
        val minutes = (secondsRead / 60).toInt()

        val finishIntent = Intent(this, SessionActionReceiver::class.java).apply {
            action = ACTION_FINISH_SESSION
            putExtra(EXTRA_TITLE, bookTitle)
            putExtra(EXTRA_AUTHOR, activeBookAuthor)
            putExtra(EXTRA_SECONDS, secondsRead)
            putExtra(EXTRA_START_EPOCH, sessionStartEpoch)
        }
        val finishPendingIntent = PendingIntent.getBroadcast(
            this, 101, finishIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val resumeIntent = Intent(this, SessionActionReceiver::class.java).apply {
            action = ACTION_CONTINUE_SESSION
        }
        val resumePendingIntent = PendingIntent.getBroadcast(
            this, 102, resumeIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_PAUSE_CONTROL)
            .setSmallIcon(android.R.drawable.ic_media_pause)
            .setContentTitle("Audible en Pausa · $minutes min registrados")
            .setContentText("'$bookTitle' · ¿Deseas terminar tu sesión de lectura?")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setOngoing(true)
            .addAction(android.R.drawable.checkbox_on_background, "Terminar Sesión", finishPendingIntent)
            .addAction(android.R.drawable.ic_media_play, "Continuar", resumePendingIntent)
            .build()

        notificationManager.notify(NOTIFICATION_PAUSE_ID, notification)
    }

    private fun dismissPauseNotification() {
        notificationManager.cancel(NOTIFICATION_PAUSE_ID)
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_PAUSE_CONTROL,
                "Control de Pausas de Lectura",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Notificaciones interactivas para confirmar o continuar sesiones de audiolibros"
            }
            notificationManager.createNotificationChannel(channel)
        }
    }

    companion object {
        const val CHANNEL_PAUSE_CONTROL = "reading_pause_control_channel"
        const val NOTIFICATION_PAUSE_ID = 4040
        const val ACTION_FINISH_SESSION = "com.universalreadingtracker.ACTION_FINISH_AUDIBLE_SESSION"
        const val ACTION_CONTINUE_SESSION = "com.universalreadingtracker.ACTION_CONTINUE_AUDIBLE_SESSION"
        const val EXTRA_TITLE = "extra_title"
        const val EXTRA_AUTHOR = "extra_author"
        const val EXTRA_SECONDS = "extra_seconds"
        const val EXTRA_START_EPOCH = "extra_start_epoch"
    }
}
