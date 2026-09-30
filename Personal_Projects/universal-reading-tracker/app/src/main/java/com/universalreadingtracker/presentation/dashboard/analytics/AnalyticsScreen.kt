package com.universalreadingtracker.presentation.dashboard.analytics

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.universalreadingtracker.domain.model.Book
import com.universalreadingtracker.domain.model.ReadingAnalytics
import com.universalreadingtracker.domain.model.ReadingGoals
import com.universalreadingtracker.domain.model.ReadingMilestone

/**
 * Dedicated Full Screen View for Annual Heatmap, Weekly Trends, Rhythm,
 * Configurable Goals (Yearly/Monthly), and Obsidian Milestones.
 * Implements RF-16 and Opción 5 (Gamificación Elegante y Metas).
 */
@Composable
fun AnalyticsScreen(
    analytics: ReadingAnalytics?,
    currentStreakDays: Int,
    activeBook: Book?,
    goals: ReadingGoals = ReadingGoals(),
    milestones: List<ReadingMilestone> = emptyList(),
    onUpdateGoals: (yearlyBooks: Int, monthlyMinutes: Int) -> Unit = { _, _ -> },
    modifier: Modifier = Modifier
) {
    var showConfigureGoalsDialog by remember { mutableStateOf(false) }
    var selectedMilestoneForDetail by remember { mutableStateOf<ReadingMilestone?>(null) }

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

        // 1. Configurable Goals (Yearly Books & Monthly Minutes)
        item {
            YearlyMonthlyGoalsCard(
                goals = goals,
                onConfigureClick = { showConfigureGoalsDialog = true }
            )
        }

        // 2. Obsidian Milestones (Gamificación Elegante)
        item {
            ObsidianMilestonesCard(
                milestones = milestones,
                onMilestoneClick = { selectedMilestoneForDetail = it }
            )
        }

        // 3. Annual Consistency Heatmap (GitHub / Obsidian style)
        item {
            AnnualConsistencyHeatmapCard(
                analytics = analytics,
                currentStreakDays = currentStreakDays
            )
        }

        // 4. Weekly Modality Trend (Audible vs. Kindle)
        item {
            WeeklyModalityChartCard(
                distribution = analytics?.weeklyDistribution
            )
        }

        // 5. Rhythm and Reading Habits
        item {
            ReadingRhythmCard(
                rhythm = analytics?.rhythmInsights,
                activeBook = activeBook
            )
        }
    }

    // Modal: Configure Goals Dialog
    if (showConfigureGoalsDialog) {
        ConfigureGoalsDialog(
            initialYearlyBooks = goals.yearlyBookGoal,
            initialMonthlyMinutes = goals.monthlyMinuteGoal,
            onDismiss = { showConfigureGoalsDialog = false },
            onSaveGoals = onUpdateGoals
        )
    }

    // Modal: Milestone Detail Dialog
    selectedMilestoneForDetail?.let { milestone ->
        MilestoneDetailDialog(
            milestone = milestone,
            onDismiss = { selectedMilestoneForDetail = null }
        )
    }
}
