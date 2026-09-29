package com.universalreadingtracker.receiver

import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import com.universalreadingtracker.data.local.AppDatabase
import com.universalreadingtracker.presentation.MainActivity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.format.DateTimeFormatter

/**
 * BroadcastReceiver triggered at 9:00 PM (Colombia Time).
 * Evaluates whether the user has read today. If not, fires a motivating high-priority notification.
 */
class ReadingReminderReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        // Automatically schedule tomorrow's 9:00 PM reminder
        ReadingReminderScheduler.scheduleDailyReminder(context)

        val pendingResult = goAsync()
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val db = AppDatabase.getInstance(context)
                val todayStr = LocalDate.now(ReadingReminderScheduler.COLOMBIA_ZONE)
                    .format(DateTimeFormatter.ISO_LOCAL_DATE)

                val todaySummary = db.dailyReadingSummaryDao().getSummaryForDate(todayStr)
                val hasReadToday = todaySummary != null && todaySummary.totalMinutesRead >= 1

                if (!hasReadToday) {
                    val streakDays = db.dailyReadingSummaryDao().countTotalValidStreakDays()
                    showStreakReminderNotification(context, streakDays)
                }
            } catch (e: Exception) {
                e.printStackTrace()
            } finally {
                pendingResult.finish()
            }
        }
    }

    private fun showStreakReminderNotification(context: Context, streakDays: Int) {
        ReadingReminderScheduler.createNotificationChannel(context)

        val openAppIntent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }

        val pendingIntent = PendingIntent.getActivity(
            context,
            ReadingReminderScheduler.REQUEST_CODE_DAILY_REMINDER,
            openAppIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val title = if (streakDays > 0) {
            "🔥 ¡Protege tu racha de $streakDays días!"
        } else {
            "📖 ¡Hora de tu lectura diaria!"
        }

        val notification = NotificationCompat.Builder(context, ReadingReminderScheduler.CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle(title)
            .setContentText("Son las 9:00 PM y aún no has leído hoy. Lee unos minutos en Kindle o dale play a Audible para no perder tu racha.")
            .setStyle(
                NotificationCompat.BigTextStyle()
                    .bigText("Son las 9:00 PM y aún no has registrado lectura hoy. Dedica 15 minutos en tu Kindle o dale play a Audible antes de medianoche para asegurar tu racha.")
            )
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_REMINDER)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()

        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(ReadingReminderScheduler.NOTIFICATION_ID, notification)
    }

    companion object {
        const val ACTION_CHECK_READING_REMINDER = "com.universalreadingtracker.ACTION_CHECK_READING_REMINDER"
    }
}
