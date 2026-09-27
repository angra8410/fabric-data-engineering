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
                    onToggleKindleTimer = { viewModel.toggleKindleReadingTimer() }
                )
            }
        }
    }
}
