package com.universalreadingtracker.presentation.dashboard.analytics

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.universalreadingtracker.domain.model.Book
import com.universalreadingtracker.domain.model.ReadingAnalytics

/**
 * Dedicated Full Screen View for Annual Heatmap, Weekly Trends, and Reading Insights.
 */
@Composable
fun AnalyticsScreen(
    analytics: ReadingAnalytics?,
    currentStreakDays: Int,
    activeBook: Book?,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
        contentPadding = PaddingValues(top = 12.dp, bottom = 28.dp)
    ) {
        item {
            Column {
                Text(
                    text = "ANÁLISIS PROFUNDO",
                    color = Color(0xFF94A3B8),
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 2.sp
                )
                Text(
                    text = "Métricas y Consistencia",
                    color = Color.White,
                    fontSize = 22.sp,
                    fontWeight = FontWeight.Black
                )
            }
        }

        // 1. Annual Consistency Heatmap
        item {
            AnnualConsistencyHeatmapCard(
                analytics = analytics,
                currentStreakDays = currentStreakDays
            )
        }

        // 2. Weekly Modality Trend (Audible vs. Kindle)
        item {
            WeeklyModalityChartCard(
                distribution = analytics?.weeklyDistribution
            )
        }

        // 3. Rhythm and Reading Habits
        item {
            ReadingRhythmCard(
                rhythm = analytics?.rhythmInsights,
                activeBook = activeBook
            )
        }
    }
}
