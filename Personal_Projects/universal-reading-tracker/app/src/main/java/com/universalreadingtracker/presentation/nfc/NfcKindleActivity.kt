package com.universalreadingtracker.presentation.nfc

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.widget.Toast
import androidx.core.content.ContextCompat
import com.universalreadingtracker.service.KindleReadingTimerService

/**
 * Implements RF-11 and ADR-011 from spec.md & decisions.md:
 * Transparent activity triggered when the user taps their phone against the NFC sticker on the Kindle cover.
 * Toggles the reading session with haptic vibration feedback without requiring UI interaction.
 */
class NfcKindleActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val isCurrentlyReading = KindleReadingTimerService.isRunning
        val serviceIntent = Intent(this, KindleReadingTimerService::class.java)

        if (!isCurrentlyReading) {
            // Start Kindle reading session
            serviceIntent.action = KindleReadingTimerService.ACTION_START
            serviceIntent.putExtra(KindleReadingTimerService.EXTRA_BOOK_TITLE, "Kindle Paperwhite / E-Reader")
            serviceIntent.putExtra(KindleReadingTimerService.EXTRA_BOOK_AUTHOR, "Kindle Físico")
            ContextCompat.startForegroundService(this, serviceIntent)

            vibrateSuccess(isStarting = true)
            Toast.makeText(this, "📖 Sesión en Kindle iniciada. ¡Buena lectura!", Toast.LENGTH_SHORT).show()
        } else {
            // Stop Kindle reading session and record progress
            serviceIntent.action = KindleReadingTimerService.ACTION_STOP
            startService(serviceIntent)

            vibrateSuccess(isStarting = false)
            Toast.makeText(this, "⏱️ Sesión finalizada. ¡Racha protegida! 🔥", Toast.LENGTH_SHORT).show()
        }

        // Close immediately to keep experience frictionless
        finish()
    }

    private fun vibrateSuccess(isStarting: Boolean) {
        val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val manager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
            manager?.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
        } ?: return

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            if (isStarting) {
                // Short single buzz for start
                vibrator.vibrate(VibrationEffect.createOneShot(120, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                // Double buzz for stop
                vibrator.vibrate(
                    VibrationEffect.createWaveform(longArrayOf(0, 100, 80, 150), -1)
                )
            }
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(200)
        }
    }
}
