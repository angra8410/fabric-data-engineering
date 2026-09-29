package com.universalreadingtracker.receiver

import android.app.AlarmManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.AlarmManagerCompat
import java.time.ZoneId
import java.time.ZonedDateTime

/**
 * Manages daily scheduling of the 9:00 PM (21:00) reading streak reminder.
 * Anchored to Colombian Time (America/Bogota, UTC-5).
 */
object ReadingReminderScheduler {

    const val CHANNEL_ID = "reading_streak_reminders"
    const val REQUEST_CODE_DAILY_REMINDER = 9001
    const val NOTIFICATION_ID = 9001
    const val DEFAULT_REMINDER_HOUR = 21
    const val DEFAULT_REMINDER_MINUTE = 0

    val COLOMBIA_ZONE: ZoneId = try {
        ZoneId.of("America/Bogota")
    } catch (e: Exception) {
        ZoneId.systemDefault()
    }

    fun createNotificationChannel(context: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Recordatorios de Racha de Lectura",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Notificaciones a las 9:00 PM (hora Colombia) si aún no has leído hoy."
                enableVibration(true)
                enableLights(true)
            }
            val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }

    fun scheduleDailyReminder(
        context: Context,
        hour: Int = DEFAULT_REMINDER_HOUR,
        minute: Int = DEFAULT_REMINDER_MINUTE
    ) {
        createNotificationChannel(context)

        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as? AlarmManager ?: return

        val now = ZonedDateTime.now(COLOMBIA_ZONE)
        var triggerZdt = now.withHour(hour).withMinute(minute).withSecond(0).withNano(0)

        // If today's 9:00 PM has already passed, schedule for tomorrow 9:00 PM
        if (now.isAfter(triggerZdt)) {
            triggerZdt = triggerZdt.plusDays(1)
        }

        val triggerEpochMillis = triggerZdt.toInstant().toEpochMilli()

        val intent = Intent(context, ReadingReminderReceiver::class.java).apply {
            action = ReadingReminderReceiver.ACTION_CHECK_READING_REMINDER
        }

        val pendingIntent = PendingIntent.getBroadcast(
            context,
            REQUEST_CODE_DAILY_REMINDER,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                if (alarmManager.canScheduleExactAlarms()) {
                    AlarmManagerCompat.setExactAndAllowWhileIdle(
                        alarmManager,
                        AlarmManager.RTC_WAKEUP,
                        triggerEpochMillis,
                        pendingIntent
                    )
                } else {
                    AlarmManagerCompat.setAndAllowWhileIdle(
                        alarmManager,
                        AlarmManager.RTC_WAKEUP,
                        triggerEpochMillis,
                        pendingIntent
                    )
                }
            } else {
                AlarmManagerCompat.setExactAndAllowWhileIdle(
                    alarmManager,
                    AlarmManager.RTC_WAKEUP,
                    triggerEpochMillis,
                    pendingIntent
                )
            }
        } catch (e: Exception) {
            e.printStackTrace()
            // Safe fallback
            alarmManager.set(
                AlarmManager.RTC_WAKEUP,
                triggerEpochMillis,
                pendingIntent
            )
        }
    }
}
