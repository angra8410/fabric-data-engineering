package com.universalreadingtracker.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/**
 * Reschedules the daily 9:00 PM reading reminder upon device boot or package update.
 */
class BootReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED ||
            intent.action == Intent.ACTION_MY_PACKAGE_REPLACED
        ) {
            ReadingReminderScheduler.scheduleDailyReminder(context)
        }
    }
}
