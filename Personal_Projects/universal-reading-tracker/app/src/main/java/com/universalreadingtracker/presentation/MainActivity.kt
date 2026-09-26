package com.universalreadingtracker.presentation

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.graphics.Color
import com.universalreadingtracker.presentation.dashboard.DashboardScreen
import com.universalreadingtracker.presentation.dashboard.DashboardViewModel

/**
 * Main Activity hosting the Jetpack Compose UI.
 */
class MainActivity : ComponentActivity() {

    private val viewModel: DashboardViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            val isDark = isSystemInDarkTheme()
            val colorScheme = if (isDark) {
                darkColorScheme(
                    primary = Color(0xFFFF9100),
                    secondary = Color(0xFF03A9F4),
                    background = Color(0xFF121212),
                    surface = Color(0xFF1E1E1E)
                )
            } else {
                lightColorScheme(
                    primary = Color(0xFFE65100),
                    secondary = Color(0xFF0288D1),
                    background = Color(0xFFF8F9FA),
                    surface = Color(0xFFFFFFFF)
                )
            }

            MaterialTheme(colorScheme = colorScheme) {
                val state by viewModel.uiState.collectAsState()
                DashboardScreen(
                    state = state,
                    onToggleKindleTimer = { viewModel.toggleKindleReadingTimer() }
                )
            }
        }
    }
}
