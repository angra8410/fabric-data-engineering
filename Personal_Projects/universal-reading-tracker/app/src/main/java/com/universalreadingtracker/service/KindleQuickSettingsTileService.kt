package com.universalreadingtracker.service

import android.content.Intent
import android.graphics.drawable.Icon
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * Quick Settings Tile in Android notification shade for 1-tap start/stop of Kindle physical reading.
 * Implements RF-03 and ADR-008 from spec.md & decisions.md.
 */
class KindleQuickSettingsTileService : TileService() {

    private var isReadingActive = false

    override fun onStartListening() {
        super.onStartListening()
        updateTileState()
    }

    override fun onClick() {
        super.onClick()
        val isCurrentlyReading = KindleReadingTimerService.isTimerActive(this)
        isReadingActive = !isCurrentlyReading

        val serviceIntent = Intent(this, KindleReadingTimerService::class.java)

        if (isReadingActive) {
            kotlinx.coroutines.CoroutineScope(kotlinx.coroutines.Dispatchers.IO).launch {
                val db = com.universalreadingtracker.data.local.AppDatabase.getInstance(applicationContext)
                val activeBook = db.bookDao().getActiveReadingBookSync()
                val title = activeBook?.title ?: "Lectura Activa en Kindle"
                val author = activeBook?.author ?: "Kindle E-Reader"

                serviceIntent.action = KindleReadingTimerService.ACTION_START
                serviceIntent.putExtra(KindleReadingTimerService.EXTRA_BOOK_TITLE, title)
                serviceIntent.putExtra(KindleReadingTimerService.EXTRA_BOOK_AUTHOR, author)
                ContextCompat.startForegroundService(applicationContext, serviceIntent)
            }
        } else {
            serviceIntent.action = KindleReadingTimerService.ACTION_STOP
            startService(serviceIntent)
        }

        updateTileState()
    }

    private fun updateTileState() {
        val tile = qsTile ?: return
        val active = KindleReadingTimerService.isTimerActive(this)
        isReadingActive = active
        tile.state = if (active) Tile.STATE_ACTIVE else Tile.STATE_INACTIVE
        tile.label = if (active) "Leyendo en Kindle..." else "Leer en Kindle"
        tile.icon = Icon.createWithResource(this, android.R.drawable.ic_menu_agenda)
        tile.updateTile()
    }
}
