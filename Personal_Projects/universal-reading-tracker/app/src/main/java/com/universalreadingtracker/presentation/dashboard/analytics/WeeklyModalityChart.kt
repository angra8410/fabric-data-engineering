package com.universalreadingtracker.presentation.dashboard.analytics

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.MenuBook
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.material.icons.filled.Headphones
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.universalreadingtracker.domain.model.WeeklyModalityDistribution

/**
 * Implements RF-16:
 * Weekly Modality Distribution Card displaying:
 * - Dual-color stacked bar chart for current week (Audible Cyan vs Kindle Amber)
 * - Proportional breakdown of hours/minutes and percentages
 * - Visual comparison of which format dominated the user's weekly reading habit
 */
@Composable
fun WeeklyModalityChartCard(
    distribution: WeeklyModalityDistribution?,
    modifier: Modifier = Modifier
) {
    val weekDays = distribution?.weekDays ?: emptyList()
    val maxDayMinutes = maxOf(45, weekDays.maxOfOrNull { it.totalMinutes } ?: 45)

    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .background(Color(0xFF111422))
            .border(1.dp, Color(0x332D323F), RoundedCornerShape(20.dp))
            .padding(16.dp)
    ) {
        Column {
            // Header
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
                            .background(Color(0x2238BDF8)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.BarChart,
                            contentDescription = "Gráfica",
                            tint = Color(0xFF38BDF8),
                            modifier = Modifier.size(18.dp)
                        )
                    }
                    Spacer(modifier = Modifier.width(10.dp))
                    Column {
                        Text(
                            text = "TENDENCIA SEMANAL",
                            color = Color(0xFF94A3B8),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 1.sp
                        )
                        Text(
                            text = "Audible vs. Kindle Físico",
                            color = Color.White,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                // Ratio badge
                val kindlePct = distribution?.kindlePercentage ?: 0
                val audioPct = distribution?.audioPercentage ?: 0
                val ratioText = if (kindlePct >= audioPct) "$kindlePct% Kindle" else "$audioPct% Audio"
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(12.dp))
                        .background(Color(0x2210B981))
                        .border(1.dp, Color(0x4410B981), RoundedCornerShape(12.dp))
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = ratioText,
                        color = Color(0xFF34D399),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Stacked Bar Chart for 7 Days
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(110.dp)
                    .padding(horizontal = 6.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Bottom
            ) {
                weekDays.forEach { item ->
                    val totalMins = item.totalMinutes
                    val barFillRatio = (totalMins.toFloat() / maxDayMinutes.toFloat()).coerceIn(0.08f, 1f)

                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier.width(36.dp)
                    ) {
                        // Minutes text above bar if read
                        if (totalMins > 0) {
                            Text(
                                text = "${totalMins}m",
                                color = if (item.isToday) Color(0xFFFBBF24) else Color(0xFF94A3B8),
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold
                            )
                        } else {
                            Spacer(modifier = Modifier.height(12.dp))
                        }

                        Spacer(modifier = Modifier.height(4.dp))

                        // Stacked Bar Container
                        Box(
                            modifier = Modifier
                                .width(18.dp)
                                .height(65.dp),
                            contentAlignment = Alignment.BottomCenter
                        ) {
                            // Background track
                            Box(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .clip(RoundedCornerShape(6.dp))
                                    .background(if (item.isFuture) Color(0xFF0F111A) else Color(0xFF1A1D2B))
                            )

                            // Actual Bar
                            if (totalMins > 0) {
                                val kindleFraction = if (totalMins > 0) item.kindleMinutes.toFloat() / totalMins.toFloat() else 0f
                                val audioFraction = if (totalMins > 0) item.audioMinutes.toFloat() / totalMins.toFloat() else 0f

                                Column(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .fillMaxHeight(barFillRatio)
                                        .clip(RoundedCornerShape(6.dp))
                                ) {
                                    // Audible portion (top)
                                    if (audioFraction > 0f) {
                                        Box(
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .weight(audioFraction)
                                                .background(Color(0xFF00E5FF))
                                        )
                                    }
                                    // Kindle portion (bottom)
                                    if (kindleFraction > 0f) {
                                        Box(
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .weight(kindleFraction)
                                                .background(Color(0xFFFF9800))
                                        )
                                    }
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(6.dp))

                        // Day Label (L, M, M, J, V, S, D)
                        Box(
                            modifier = Modifier
                                .size(22.dp)
                                .clip(CircleShape)
                                .background(if (item.isToday) Color(0xFF38BDF8) else Color.Transparent),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = item.dayLabel,
                                color = if (item.isToday) Color(0xFF090A10) else if (item.isFuture) Color(0xFF475569) else Color(0xFFE2E8F0),
                                fontSize = 11.sp,
                                fontWeight = if (item.isToday) FontWeight.Black else FontWeight.Bold
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Modality Legend & Totals Row
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(Color(0xFF161928))
                    .padding(horizontal = 14.dp, vertical = 10.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Kindle Stat
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(10.dp).clip(CircleShape).background(Color(0xFFFF9800)))
                    Spacer(modifier = Modifier.width(6.dp))
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.MenuBook,
                        contentDescription = "Kindle",
                        tint = Color(0xFFFF9800),
                        modifier = Modifier.size(14.dp)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = "Kindle: ${distribution?.totalKindleMinutes ?: 0} min (${distribution?.kindlePercentage ?: 0}%)",
                        color = Color(0xFFE2E8F0),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium
                    )
                }

                // Audible Stat
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(10.dp).clip(CircleShape).background(Color(0xFF00E5FF)))
                    Spacer(modifier = Modifier.width(6.dp))
                    Icon(
                        imageVector = Icons.Default.Headphones,
                        contentDescription = "Audible",
                        tint = Color(0xFF00E5FF),
                        modifier = Modifier.size(14.dp)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = "Audible: ${distribution?.totalAudioMinutes ?: 0} min (${distribution?.audioPercentage ?: 0}%)",
                        color = Color(0xFFE2E8F0),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }
    }
}
