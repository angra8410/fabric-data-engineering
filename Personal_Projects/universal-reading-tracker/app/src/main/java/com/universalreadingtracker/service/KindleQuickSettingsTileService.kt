package com.universalreadingtracker.service

import android.content.Intent
import android.graphics.drawable.Icon
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService
import androidx.core.content.ContextCompat

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
        isReadingActive = !isReadingActive

        val serviceIntent = Intent(this, KindleReadingTimerService::class.java).apply {
            action = if (isReadingActive) KindleReadingTimerService.ACTION_START else KindleReadingTimerService.ACTION_STOP
            if (isReadingActive) {
                putExtra(KindleReadingTimerService.EXTRA_BOOK_TITLE, "Lectura Activa en Kindle")
                putExtra(KindleReadingTimerService.EXTRA_BOOK_AUTHOR, "Kindle E-Reader")
            }
        }

        ContextCompat.startForegroundService(this, serviceIntent)
        updateTileState()
    }

    private fun updateTileState() {
        val tile = qsTile ?: return
        tile.state = if (isReadingActive) Tile.STATE_ACTIVE else Tile.STATE_INACTIVE
        tile.label = if (isReadingActive) "Leyendo en Kindle..." else "Leer en Kindle"
        tile.icon = Icon.createWithResource(this, android.R.drawable.ic_menu_agenda)
        tile.updateTile()
    }
}
