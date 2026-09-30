package com.universalreadingtracker.presentation.dashboard.analytics

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.Info
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.universalreadingtracker.domain.model.DayContribution
import com.universalreadingtracker.domain.model.ReadingAnalytics
import java.time.DayOfWeek
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.temporal.TemporalAdjusters
import java.util.Locale

/**
 * Implements RF-16 & ADR-020:
 * Annual Consistency Heatmap (GitHub/Obsidian style) displaying:
 * - 52-week horizontal matrix of reading contributions
 * - Intensity scale in Emerald Obsidian (#1E2230 -> #064E3B -> #059669 -> #10B981 -> #34D399)
 * - Interactive tap to inspect date, minutes read, and modality breakdown
 * - Cumulative 164+ day streak historical baseline reflection
 */
@Composable
fun AnnualConsistencyHeatmapCard(
    analytics: ReadingAnalytics?,
    currentStreakDays: Int,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    var selectedDay by remember { mutableStateOf<DayContribution?>(null) }
    val today = remember { LocalDate.now() }
    val dateFormatter = remember { DateTimeFormatter.ISO_LOCAL_DATE }
    val displayDateFormatter = remember { DateTimeFormatter.ofPattern("EEEE d 'de' MMMM, yyyy", Locale.forLanguageTag("es-CO")) }

    // Generate last 36 weeks (or up to today) aligned to Monday
    val weeksData = remember(analytics, today) {
        val endDate = today.with(TemporalAdjusters.nextOrSame(DayOfWeek.SUNDAY))
        val startDate = endDate.minusWeeks(35).with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY))

        val weeks = mutableListOf<List<LocalDate>>()
        var curr = startDate
        while (!curr.isAfter(endDate)) {
            val weekDays = mutableListOf<LocalDate>()
            for (d in 0..6) {
                weekDays.add(curr.plusDays(d.toLong()))
            }
            weeks.add(weekDays)
            curr = curr.plusWeeks(1)
        }
        weeks
    }

    // Scroll to the end (current date) automatically
    LaunchedEffect(weeksData) {
        scrollState.scrollTo(scrollState.maxValue)
    }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .background(Color(0xFF111422))
            .border(1.dp, Color(0x332D323F), RoundedCornerShape(20.dp))
            .padding(16.dp)
    ) {
        Column {
            // Header: Title & Badges
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(32.dp)
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0x2210B981)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.CalendarMonth,
                            contentDescription = "Calendario",
                            tint = Color(0xFF10B981),
                            modifier = Modifier.size(18.dp)
                        )
                    }
                    Spacer(modifier = Modifier.width(10.dp))
                    Column {
                        Text(
                            text = "MAPA DE CONSISTENCIA",
                            color = Color(0xFF94A3B8),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 1.sp
                        )
                        Text(
                            text = "Matriz de Hábitos 2026",
                            color = Color.White,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                // Summary Badge (Total Hours)
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(12.dp))
                        .background(Color(0x22F59E0B))
                        .border(1.dp, Color(0x44F59E0B), RoundedCornerShape(12.dp))
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = "⏱ ${(analytics?.totalHoursRead ?: 0f)}h en el año",
                        color = Color(0xFFFBBF24),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Subtitle stats row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "🔥 $currentStreakDays días activos consecutivos",
                    color = Color(0xFFE2E8F0),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = "${analytics?.totalDaysWithReading ?: currentStreakDays} días con lectura",
                    color = Color(0xFF38BDF8),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Heatmap Grid Container with Horizontal Scroll
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .horizontalScroll(scrollState),
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                // Day Labels Column (L, M, V, D)
                Column(
                    verticalArrangement = Arrangement.spacedBy(4.dp),
                    modifier = Modifier.padding(end = 4.dp, top = 2.dp)
                ) {
                    val dayLabels = listOf("L", "M", "M", "J", "V", "S", "D")
                    dayLabels.forEachIndexed { idx, label ->
                        // Show only alternate labels for clean look
                        if (idx == 0 || idx == 2 || idx == 4 || idx == 6) {
                            Text(
                                text = label,
                                color = Color(0xFF64748B),
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.height(13.dp)
                            )
                        } else {
                            Spacer(modifier = Modifier.height(13.dp))
                        }
                    }
                }

                // Weeks Columns
                weeksData.forEach { week ->
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        week.forEach { date ->
                            val dateStr = date.format(dateFormatter)
                            val contrib = analytics?.heatmapContributions?.get(dateStr)
                            val level = contrib?.intensityLevel ?: 0
                            val isFuture = date.isAfter(today)
                            val isToday = date == today

                            val cellColor = when {
                                isFuture -> Color(0xFF0F111A)
                                level == 0 -> Color(0xFF1E2230)
                                level == 1 -> Color(0xFF064E3B)
                                level == 2 -> Color(0xFF059669)
                                level == 3 -> Color(0xFF10B981)
                                else -> Color(0xFF34D399) // Level 4
                            }

                            val isSelected = selectedDay?.date == dateStr

                            Box(
                                modifier = Modifier
                                    .size(13.dp)
                                    .clip(RoundedCornerShape(3.dp))
                                    .background(cellColor)
                                    .then(
                                        if (isSelected) {
                                            Modifier.border(1.5.dp, Color(0xFFFBBF24), RoundedCornerShape(3.dp))
                                        } else if (isToday) {
                                            Modifier.border(1.dp, Color(0xFF38BDF8), RoundedCornerShape(3.dp))
                                        } else {
                                            Modifier
                                        }
                                    )
                                    .clickable(enabled = !isFuture) {
                                        selectedDay = contrib ?: DayContribution(
                                            date = dateStr,
                                            totalMinutes = 0,
                                            audioMinutes = 0,
                                            kindleMinutes = 0,
                                            physicalMinutes = 0,
                                            intensityLevel = 0
                                        )
                                    }
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Legend & Inspection Banner
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Toca un día para ver detalle",
                    color = Color(0xFF64748B),
                    fontSize = 11.sp
                )

                // Color Intensity Legend
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(3.dp)
                ) {
                    Text(text = "Menos", color = Color(0xFF64748B), fontSize = 10.sp)
                    Box(modifier = Modifier.size(10.dp).clip(RoundedCornerShape(2.dp)).background(Color(0xFF1E2230)))
                    Box(modifier = Modifier.size(10.dp).clip(RoundedCornerShape(2.dp)).background(Color(0xFF064E3B)))
                    Box(modifier = Modifier.size(10.dp).clip(RoundedCornerShape(2.dp)).background(Color(0xFF059669)))
                    Box(modifier = Modifier.size(10.dp).clip(RoundedCornerShape(2.dp)).background(Color(0xFF10B981)))
                    Box(modifier = Modifier.size(10.dp).clip(RoundedCornerShape(2.dp)).background(Color(0xFF34D399)))
                    Text(text = "Más", color = Color(0xFF64748B), fontSize = 10.sp)
                }
            }

            // Interactive Day Detail Card when tapped
            AnimatedVisibility(visible = selectedDay != null) {
                selectedDay?.let { day ->
                    val parsedDate = try { LocalDate.parse(day.date, dateFormatter) } catch (_: Exception) { null }
                    val formattedDate = parsedDate?.format(displayDateFormatter)?.replaceFirstChar { it.uppercase() } ?: day.date

                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 10.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(Color(0xFF161928))
                            .border(1.dp, Color(0x3338BDF8), RoundedCornerShape(12.dp))
                            .padding(12.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Column {
                                Text(
                                    text = formattedDate,
                                    color = Color(0xFFE2E8F0),
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold
                                )
                                Spacer(modifier = Modifier.height(2.dp))
                                Text(
                                    text = if (day.totalMinutes > 0) {
                                        "📖 ${day.totalMinutes} min totales (${day.kindleMinutes}m Kindle • ${day.audioMinutes}m Audible)"
                                    } else {
                                        "Sin lectura registrada"
                                    },
                                    color = if (day.totalMinutes > 0) Color(0xFF34D399) else Color(0xFF94A3B8),
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Medium
                                )
                            }

                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(Color(0x33FFFFFF))
                                    .clickable { selectedDay = null }
                                    .padding(horizontal = 8.dp, vertical = 4.dp)
                            ) {
                                Text(text = "✕", color = Color(0xFF94A3B8), fontSize = 11.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }
        }
    }
}
