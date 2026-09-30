package com.universalreadingtracker.presentation

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.nfc.NfcAdapter
import android.nfc.Tag
import android.nfc.tech.Ndef
import android.os.Build
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.graphics.Color
import com.universalreadingtracker.presentation.dashboard.DashboardScreen
import com.universalreadingtracker.presentation.dashboard.DashboardViewModel
import com.universalreadingtracker.presentation.nfc.NfcWriterHelper
import com.universalreadingtracker.presentation.widget.ReadingAppWidgetProvider

/**
 * Main Activity hosting the Jetpack Compose UI.
 * Handles NFC Foreground Dispatch:
 * - If tag is new: programs "readingtracker://kindle" and activates reading.
 * - If tag is already programmed: toggles reading session immediately with haptic feedback.
 */
class MainActivity : ComponentActivity() {

    private val viewModel: DashboardViewModel by viewModels()
    private var nfcAdapter: NfcAdapter? = null
    private var nfcPendingIntent: PendingIntent? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        nfcAdapter = NfcAdapter.getDefaultAdapter(this)
        val intent = Intent(this, javaClass).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
        nfcPendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_MUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        if (Build.VERSION.SDK_INT >= 34) {
            overrideActivityTransition(
                OVERRIDE_TRANSITION_OPEN,
                android.R.anim.fade_in,
                android.R.anim.fade_out
            )
        } else {
            @Suppress("DEPRECATION")
            overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) !=
                android.content.pm.PackageManager.PERMISSION_GRANTED
            ) {
                requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 101)
            }
        }

        setContent {
            val colorScheme = darkColorScheme(
                primary = Color(0xFFFF5E36),
                secondary = Color(0xFF00E5FF),
                tertiary = Color(0xFFA855F7),
                background = Color(0xFF090A10),
                surface = Color(0xFF131522),
                onBackground = Color(0xFFF1F5F9),
                onSurface = Color(0xFFF1F5F9)
            )

            MaterialTheme(colorScheme = colorScheme) {
                val state by viewModel.uiState.collectAsState()
                DashboardScreen(
                    state = state,
                    onToggleKindleTimer = { viewModel.toggleKindleReadingTimer() },
                    onSelectBook = { bookId -> 
                        viewModel.selectActiveBook(bookId)
                        ReadingAppWidgetProvider.updateAllWidgets(this@MainActivity)
                    },
                    onAddNewBook = { title, author, unit, curPos, total ->
                        viewModel.addNewBook(title, author, unit, curPos, total)
                        ReadingAppWidgetProvider.updateAllWidgets(this@MainActivity)
                    },
                    onUpdatePosition = { newPos -> 
                        viewModel.updateActiveBookPosition(newPos)
                        ReadingAppWidgetProvider.updateAllWidgets(this@MainActivity)
                    },
                    onUpdateBookPosition = { bookId, newPos ->
                        viewModel.updateBookPosition(bookId, newPos)
                        ReadingAppWidgetProvider.updateAllWidgets(this@MainActivity)
                    },
                    onExportJson = { viewModel.exportDataToJson(this@MainActivity) },
                    onSyncCatalog = { viewModel.syncEnrichedCatalogFromAssets() },
                    onSaveSessionNotes = { sessionId, notes -> viewModel.saveSessionNotes(sessionId, notes) },
                    onAddHighlight = { bookId, title, author, note, page ->
                        viewModel.addHighlightOrNote(bookId, title, author, note, page)
                    }
                )
            }
        }
    }

    override fun onResume() {
        super.onResume()
        viewModel.syncTimerState()
        ReadingAppWidgetProvider.updateAllWidgets(this)
        nfcPendingIntent?.let { pendingIntent ->
            nfcAdapter?.enableForegroundDispatch(this, pendingIntent, null, null)
        }
    }

    override fun onPause() {
        super.onPause()
        nfcAdapter?.disableForegroundDispatch(this)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        if (NfcAdapter.ACTION_TAG_DISCOVERED == intent.action ||
            NfcAdapter.ACTION_NDEF_DISCOVERED == intent.action ||
            NfcAdapter.ACTION_TECH_DISCOVERED == intent.action
        ) {
            val tag: Tag? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                intent.getParcelableExtra(NfcAdapter.EXTRA_TAG, Tag::class.java)
            } else {
                @Suppress("DEPRECATION")
                intent.getParcelableExtra(NfcAdapter.EXTRA_TAG)
            }

            if (tag != null) {
                handleScannedTag(tag)
            }
        }
    }

    private fun handleScannedTag(tag: Tag) {
        var isAlreadyProgrammed = false
        val ndef = Ndef.get(tag)
        if (ndef != null) {
            try {
                ndef.connect()
                val msg = ndef.ndefMessage
                val uri = msg?.records?.firstOrNull()?.toUri()?.toString()
                if (uri == NfcWriterHelper.KINDLE_TRIGGER_URI) {
                    isAlreadyProgrammed = true
                }
                ndef.close()
            } catch (_: Exception) {
                // Ignore connection read error, fallback to write
            }
        }

        if (isAlreadyProgrammed) {
            // Already a Kindle tracker tag: toggle session directly!
            viewModel.toggleKindleReadingTimer()
            vibrateFeedback()
            Toast.makeText(this, "⚡ NFC: Sesión de lectura conmutada", Toast.LENGTH_SHORT).show()
        } else {
            // Unprogrammed tag: write URI first, then toggle session!
            val writeResult = NfcWriterHelper.writeKindleTag(tag)
            if (writeResult.isSuccess) {
                viewModel.toggleKindleReadingTimer()
                vibrateFeedback()
                Toast.makeText(
                    this,
                    "✨ ¡Sticker NFC programado y lectura iniciada!",
                    Toast.LENGTH_LONG
                ).show()
            } else {
                val errorMsg = writeResult.exceptionOrNull()?.message ?: "Error desconocido"
                Toast.makeText(
                    this,
                    "⚠️ Error al escribir en sticker: $errorMsg",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }

    private fun vibrateFeedback() {
        val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val manager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
            manager?.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
        } ?: return

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createOneShot(120, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(150)
        }
    }
}
