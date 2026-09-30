package com.universalreadingtracker.presentation.dashboard.analytics

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.universalreadingtracker.domain.model.Book
import com.universalreadingtracker.domain.model.ReadingAnalytics

enum class AnalyticsTab(val title: String, val emoji: String) {
    HEATMAP("Consistencia", "🟩"),
    WEEKLY("Audible vs Kindle", "📊"),
    RHYTHM("Ritmo & Horario", "⚡")
}

/**
 * Implements RF-16 & ADR-020:
 * Container section hosting the Annual Consistency Heatmap, Weekly Modality Trend,
 * and Reading Rhythm insights with Obsidian Luxury tab switching.
 */
@Composable
fun ReadingAnalyticsSection(
    analytics: ReadingAnalytics?,
    currentStreakDays: Int,
    activeBook: Book?,
    modifier: Modifier = Modifier
) {
    var selectedTab by remember { mutableStateOf(AnalyticsTab.HEATMAP) }

    Column(modifier = modifier.fillMaxWidth()) {
        // Section Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Analítica & Consistencia",
                color = Color(0xFFE2E8F0),
                fontSize = 15.sp,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = "Métricas 2026",
                color = Color(0xFF94A3B8),
                fontSize = 12.sp,
                fontWeight = FontWeight.Medium
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        // Luxury Tab Selector Pills
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(Color(0xFF0F121E))
                .padding(3.dp),
            horizontalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            AnalyticsTab.values().forEach { tab ->
                val isSelected = selectedTab == tab
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .clip(RoundedCornerShape(12.dp))
                        .background(if (isSelected) Color(0xFF1E2337) else Color.Transparent)
                        .then(
                            if (isSelected) Modifier.border(1.dp, Color(0x33FFFFFF), RoundedCornerShape(12.dp))
                            else Modifier
                        )
                        .clickable { selectedTab = tab }
                        .padding(vertical = 8.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(text = tab.emoji, fontSize = 11.sp)
                        Spacer(modifier = Modifier.width(5.dp))
                        Text(
                            text = tab.title,
                            color = if (isSelected) Color.White else Color(0xFF94A3B8),
                            fontSize = 11.sp,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Tab Content Display with Smooth Crossfade
        AnimatedContent(
            targetState = selectedTab,
            transitionSpec = { fadeIn() togetherWith fadeOut() },
            label = "AnalyticsTabTransition"
        ) { tab ->
            when (tab) {
                AnalyticsTab.HEATMAP -> {
                    AnnualConsistencyHeatmapCard(
                        analytics = analytics,
                        currentStreakDays = currentStreakDays
                    )
                }
                AnalyticsTab.WEEKLY -> {
                    WeeklyModalityChartCard(
                        distribution = analytics?.weeklyDistribution
                    )
                }
                AnalyticsTab.RHYTHM -> {
                    ReadingRhythmCard(
                        rhythm = analytics?.rhythmInsights,
                        activeBook = activeBook
                    )
                }
            }
        }
    }
}
