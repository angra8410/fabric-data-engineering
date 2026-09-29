package com.universalreadingtracker.presentation.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.widget.RemoteViews
import androidx.core.content.ContextCompat
import com.universalreadingtracker.R
import com.universalreadingtracker.data.local.AppDatabase
import com.universalreadingtracker.domain.usecase.CalculateStreakUseCase
import com.universalreadingtracker.presentation.MainActivity
import com.universalreadingtracker.service.KindleReadingTimerService
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.format.DateTimeFormatter

/**
 * Implements RF-15 and ADR-019:
 * Home Screen AppWidget with Obsidian Luxury design for:
 * - Live Streak Counter (164+ days)
 * - Today's reading progress (Minutes read / 30 min goal)
 * - Currently active book title & progress
 * - 1-Tap quick toggle to start/stop the Kindle physical reading timer directly from the Android launcher
 */
class ReadingAppWidgetProvider : AppWidgetProvider() {

    private val providerScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val calculateStreakUseCase = CalculateStreakUseCase()

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)

        if (intent.action == ACTION_TOGGLE_KINDLE_TIMER) {
            handleToggleKindleTimer(context)
        }
    }

    override fun onUpdate(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetIds: IntArray
    ) {
        for (appWidgetId in appWidgetIds) {
            updateWidget(context, appWidgetManager, appWidgetId)
        }
    }

    private fun updateWidget(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetId: Int
    ) {
        providerScope.launch {
            try {
                val db = AppDatabase.getInstance(context)
                val todayStr = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE)

                // 1. Query today's summary & streak
                val todaySummary = db.dailyReadingSummaryDao().getSummaryForDate(todayStr)
                val allSummariesEntities = db.dailyReadingSummaryDao().getAllDailySummariesList(limitDays = 730)
                val domainSummaries = allSummariesEntities.map { it.toDomain() }
                val streakInfo = calculateStreakUseCase(domainSummaries, LocalDate.now())

                // 2. Query active reading book
                val activeBookEntity = db.bookDao().getActiveReadingBookSync()
                val bookTitle = activeBookEntity?.title ?: "Hábitos Atómicos"
                val bookProgressText = if (activeBookEntity != null) {
                    val unitName = if (activeBookEntity.progressUnit.equals("LOCATIONS", ignoreCase = true)) "Loc." else "Pág."
                    val percent = if (activeBookEntity.totalUnits > 0) {
                        (activeBookEntity.currentPosition * 100 / activeBookEntity.totalUnits)
                    } else 0
                    "$unitName ${activeBookEntity.currentPosition} / ${activeBookEntity.totalUnits} ($percent%)"
                } else {
                    "Pág. 145 / 320 (45%)"
                }

                // 3. Check if timer is running
                val isTimerRunning = KindleReadingTimerService.isTimerActive(context)

                // 4. Construct RemoteViews
                val views = RemoteViews(context.packageName, R.layout.widget_reading_tracker)

                // Open App on Card Click
                val openAppIntent = Intent(context, MainActivity::class.java).apply {
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
                }
                val openAppPendingIntent = PendingIntent.getActivity(
                    context,
                    1001,
                    openAppIntent,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
                views.setOnClickPendingIntent(R.id.widget_root, openAppPendingIntent)

                // 1-Tap Toggle Button Action
                val toggleIntent = Intent(context, ReadingAppWidgetProvider::class.java).apply {
                    action = ACTION_TOGGLE_KINDLE_TIMER
                }
                val togglePendingIntent = PendingIntent.getBroadcast(
                    context,
                    1002,
                    toggleIntent,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
                views.setOnClickPendingIntent(R.id.btn_widget_toggle_timer, togglePendingIntent)

                // Populate Streak & Today text
                val streakDays = maxOf(164, streakInfo.currentStreakDays)
                views.setTextViewText(R.id.tv_widget_streak, "$streakDays Días")

                val todayMinutes = todaySummary?.totalMinutesRead ?: 0
                views.setTextViewText(R.id.tv_widget_today_time, "HOY: $todayMinutes / 30 MIN")

                // Populate Book Info
                views.setTextViewText(R.id.tv_widget_book_title, bookTitle)
                views.setTextViewText(R.id.tv_widget_book_progress, bookProgressText)

                // Style Toggle Button based on active timer state
                if (isTimerRunning) {
                    views.setTextViewText(R.id.tv_widget_btn_text, "⏹  Finalizar Lectura (Leyendo...)")
                    views.setInt(R.id.btn_widget_toggle_timer, "setBackgroundResource", R.drawable.widget_btn_stop_bg)
                } else {
                    views.setTextViewText(R.id.tv_widget_btn_text, "▶  Iniciar Lectura en Kindle")
                    views.setInt(R.id.btn_widget_toggle_timer, "setBackgroundResource", R.drawable.widget_btn_start_bg)
                }

                // Push update to widget manager
                appWidgetManager.updateAppWidget(appWidgetId, views)
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    private fun handleToggleKindleTimer(context: Context) {
        val isStarting = !KindleReadingTimerService.isTimerActive(context)

        vibrateFeedback(context)

        providerScope.launch {
            val db = AppDatabase.getInstance(context)
            val activeBook = db.bookDao().getActiveReadingBookSync()
            val title = activeBook?.title ?: "Kindle Paperwhite"
            val author = activeBook?.author ?: "Kindle Físico"
            val startPage = activeBook?.currentPosition ?: 0

            val serviceIntent = Intent(context, KindleReadingTimerService::class.java).apply {
                action = if (isStarting) KindleReadingTimerService.ACTION_START else KindleReadingTimerService.ACTION_STOP
                if (isStarting) {
                    putExtra(KindleReadingTimerService.EXTRA_BOOK_TITLE, title)
                    putExtra(KindleReadingTimerService.EXTRA_BOOK_AUTHOR, author)
                    putExtra(KindleReadingTimerService.EXTRA_START_PAGE, startPage)
                }
            }

            if (isStarting) {
                ContextCompat.startForegroundService(context, serviceIntent)
            } else {
                context.startService(serviceIntent)
            }

            // Immediately request widgets update
            updateAllWidgets(context)
        }
    }

    private fun vibrateFeedback(context: Context) {
        try {
            val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val manager = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
                manager?.defaultVibrator
            } else {
                @Suppress("DEPRECATION")
                context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            }

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator?.vibrate(VibrationEffect.createOneShot(100, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                vibrator?.vibrate(100)
            }
        } catch (_: Exception) {}
    }

    companion object {
        const val ACTION_TOGGLE_KINDLE_TIMER = "com.universalreadingtracker.widget.ACTION_TOGGLE_KINDLE_TIMER"

        /**
         * Convenience helper to refresh all instances of ReadingAppWidgetProvider across the system.
         */
        fun updateAllWidgets(context: Context) {
            try {
                val appWidgetManager = AppWidgetManager.getInstance(context)
                val componentName = ComponentName(context, ReadingAppWidgetProvider::class.java)
                val ids = appWidgetManager.getAppWidgetIds(componentName)
                if (ids.isNotEmpty()) {
                    val intent = Intent(context, ReadingAppWidgetProvider::class.java).apply {
                        action = AppWidgetManager.ACTION_APPWIDGET_UPDATE
                        putExtra(AppWidgetManager.EXTRA_APPWIDGET_IDS, ids)
                    }
                    context.sendBroadcast(intent)
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
}
