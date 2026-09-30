package com.universalreadingtracker.presentation.dashboard.analytics

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Remove
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import com.universalreadingtracker.domain.model.ReadingGoals
import com.universalreadingtracker.domain.model.ReadingMilestone
import java.util.Locale

/**
 * Card displaying configurable yearly and monthly reading goals with Obsidian Luxury gauges.
 * Implements Opción 5 (Metas Anuales / Mensuales).
 */
@Composable
fun YearlyMonthlyGoalsCard(
    goals: ReadingGoals,
    onConfigureClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .shadow(12.dp, RoundedCornerShape(22.dp), ambientColor = Color(0x33000000)),
        shape = RoundedCornerShape(22.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF111422))
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "METAS & OBJETIVOS",
                        color = Color(0xFF94A3B8),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 2.sp
                    )
                    Text(
                        text = "Compromiso Lector",
                        color = Color.White,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Black
                    )
                }

                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(20.dp))
                        .background(Color(0x2238BDF8))
                        .border(1.dp, Color(0x5538BDF8), RoundedCornerShape(20.dp))
                        .clickable { onConfigureClick() }
                        .padding(horizontal = 10.dp, vertical = 6.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.Settings,
                            contentDescription = "Configurar",
                            tint = Color(0xFF38BDF8),
                            modifier = Modifier.size(13.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = "Ajustar",
                            color = Color(0xFF38BDF8),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                }
            }

            // Goal 1: Yearly Books Goal
            GoalProgressItem(
                icon = "📚",
                title = "Meta Anual (${goals.currentYear})",
                currentValueText = "${goals.completedBooksThisYear} de ${goals.yearlyBookGoal} libros",
                subCaption = if (goals.completedBooksThisYear >= goals.yearlyBookGoal)
                    "¡Objetivo anual alcanzado! 🎉"
                else
                    "Faltan ${goals.remainingBooks} libro(s) para culminar",
                progressPercent = goals.yearlyProgressPercent,
                barColor = Color(0xFFFBBF24), // Obsidian Gold
                percentText = "${(goals.yearlyProgressPercent * 100).toInt()}%"
            )

            HorizontalDivider(color = Color(0xFF1E2538), thickness = 1.dp)

            // Goal 2: Monthly Minutes Goal
            val hoursRead = (goals.minutesReadThisMonth / 60f)
            val hoursString = String.format(Locale.ROOT, "%.1fh", hoursRead)
            GoalProgressItem(
                icon = "⏱️",
                title = "Minutos en ${goals.currentMonthName}",
                currentValueText = "${goals.minutesReadThisMonth} de ${goals.monthlyMinuteGoal} min",
                subCaption = if (goals.minutesReadThisMonth >= goals.monthlyMinuteGoal)
                    "¡Meta mensual superada con éxito! ($hoursString) 🚀"
                else
                    "$hoursString acumuladas • Faltan ${goals.remainingMinutesThisMonth} min",
                progressPercent = goals.monthlyProgressPercent,
                barColor = Color(0xFF38BDF8), // Electric Cyan
                percentText = "${(goals.monthlyProgressPercent * 100).toInt()}%"
            )
        }
    }
}

@Composable
private fun GoalProgressItem(
    icon: String,
    title: String,
    currentValueText: String,
    subCaption: String,
    progressPercent: Float,
    barColor: Color,
    percentText: String
) {
    val animatedProgress by animateFloatAsState(
        targetValue = progressPercent.coerceIn(0f, 1f),
        animationSpec = tween(durationMillis = 600),
        label = "GoalProgressAnimation"
    )

    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(text = icon, fontSize = 16.sp)
                Spacer(modifier = Modifier.width(8.dp))
                Column {
                    Text(
                        text = title,
                        color = Color(0xFFE2E8F0),
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                    Text(
                        text = subCaption,
                        color = Color(0xFF94A3B8),
                        fontSize = 11.sp
                    )
                }
            }

            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = currentValueText,
                    color = Color.White,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = percentText,
                    color = barColor,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Black
                )
            }
        }

        // Progress Bar
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(8.dp)
                .clip(RoundedCornerShape(4.dp))
                .background(Color(0xFF1E2538))
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth(animatedProgress)
                    .fillMaxHeight()
                    .clip(RoundedCornerShape(4.dp))
                    .background(
                        Brush.horizontalGradient(
                            listOf(barColor.copy(alpha = 0.7f), barColor)
                        )
                    )
            )
        }
    }
}

/**
 * Card displaying the 4 Obsidian Milestones (Gamificación Elegante).
 */
@Composable
fun ObsidianMilestonesCard(
    milestones: List<ReadingMilestone>,
    onMilestoneClick: (ReadingMilestone) -> Unit,
    modifier: Modifier = Modifier
) {
    val unlockedCount = milestones.count { it.isUnlocked }

    Card(
        modifier = modifier
            .fillMaxWidth()
            .shadow(12.dp, RoundedCornerShape(22.dp), ambientColor = Color(0x33000000)),
        shape = RoundedCornerShape(22.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF111422))
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "GAMIFICACIÓN ELEGANTE",
                        color = Color(0xFF94A3B8),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 2.sp
                    )
                    Text(
                        text = "Insignias & Milestones",
                        color = Color.White,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Black
                    )
                }

                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(12.dp))
                        .background(Color(0xFF1A1F33))
                        .border(1.dp, Color(0xFFFBBF24).copy(alpha = 0.4f), RoundedCornerShape(12.dp))
                        .padding(horizontal = 9.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = "$unlockedCount de ${milestones.size} Conquistados ✨",
                        color = Color(0xFFFBBF24),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            // 2x2 Grid of Milestones
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                for (chunk in milestones.chunked(2)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        for (milestone in chunk) {
                            MilestonePillCard(
                                milestone = milestone,
                                onClick = { onMilestoneClick(milestone) },
                                modifier = Modifier.weight(1f)
                            )
                        }
                        if (chunk.size == 1) {
                            Spacer(modifier = Modifier.weight(1f))
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun MilestonePillCard(
    milestone: ReadingMilestone,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val borderColor = if (milestone.isUnlocked) {
        Color(0xFFFBBF24).copy(alpha = 0.6f)
    } else {
        Color(0x33252C48)
    }

    val cardBg = if (milestone.isUnlocked) {
        Color(0xFF14192A)
    } else {
        Color(0xFF0F121C)
    }

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .background(cardBg)
            .border(1.dp, borderColor, RoundedCornerShape(16.dp))
            .clickable { onClick() }
            .padding(14.dp)
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(36.dp)
                        .clip(CircleShape)
                        .background(
                            if (milestone.isUnlocked) Color(0x33FBBF24) else Color(0xFF1E2538)
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = milestone.iconEmoji,
                        fontSize = 18.sp
                    )
                }

                if (milestone.isUnlocked) {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(6.dp))
                            .background(Color(0x3310B981))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = "DESBLOQUEADO",
                            color = Color(0xFF10B981),
                            fontSize = 8.sp,
                            fontWeight = FontWeight.Black,
                            letterSpacing = 0.5.sp
                        )
                    }
                } else {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(6.dp))
                            .background(Color(0xFF1E2538))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = "EN CURSO",
                            color = Color(0xFF94A3B8),
                            fontSize = 8.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 0.5.sp
                        )
                    }
                }
            }

            Text(
                text = milestone.title,
                color = if (milestone.isUnlocked) Color.White else Color(0xFFCBD5E1),
                fontSize = 13.sp,
                fontWeight = FontWeight.Bold,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )

            Text(
                text = milestone.progressLabel,
                color = if (milestone.isUnlocked) Color(0xFFFBBF24) else Color(0xFF64748B),
                fontSize = 11.sp,
                fontWeight = FontWeight.Medium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}

/**
 * Dialog to adjust Yearly Book Goal and Monthly Minute Goal.
 */
@Composable
fun ConfigureGoalsDialog(
    initialYearlyBooks: Int,
    initialMonthlyMinutes: Int,
    onDismiss: () -> Unit,
    onSaveGoals: (yearlyBooks: Int, monthlyMinutes: Int) -> Unit
) {
    var yearlyBooks by remember { mutableIntStateOf(initialYearlyBooks) }
    var monthlyMinutes by remember { mutableIntStateOf(initialMonthlyMinutes) }

    Dialog(onDismissRequest = onDismiss) {
        Card(
            shape = RoundedCornerShape(24.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF111422)),
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, Color(0xFF2D323F), RoundedCornerShape(24.dp))
                .padding(4.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp),
                verticalArrangement = Arrangement.spacedBy(20.dp)
            ) {
                // Header
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "CONFIGURACIÓN",
                            color = Color(0xFF94A3B8),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 2.sp
                        )
                        Text(
                            text = "Metas de Lectura",
                            color = Color.White,
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Black
                        )
                    }

                    IconButton(
                        onClick = onDismiss,
                        modifier = Modifier.size(28.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Close,
                            contentDescription = "Cerrar",
                            tint = Color(0xFF94A3B8)
                        )
                    }
                }

                // 1. Yearly Books Setting
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        text = "Meta Anual de Libros (2026)",
                        color = Color(0xFFE2E8F0),
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        IconButton(
                            onClick = { if (yearlyBooks > 1) yearlyBooks-- },
                            modifier = Modifier
                                .size(40.dp)
                                .clip(CircleShape)
                                .background(Color(0xFF1E2538))
                        ) {
                            Icon(Icons.Default.Remove, contentDescription = "-1 libro", tint = Color.White)
                        }

                        Text(
                            text = "$yearlyBooks libros",
                            color = Color(0xFFFBBF24),
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Black
                        )

                        IconButton(
                            onClick = { yearlyBooks++ },
                            modifier = Modifier
                                .size(40.dp)
                                .clip(CircleShape)
                                .background(Color(0xFF1E2538))
                        ) {
                            Icon(Icons.Default.Add, contentDescription = "+1 libro", tint = Color.White)
                        }
                    }
                }

                HorizontalDivider(color = Color(0xFF1E2538))

                // 2. Monthly Minutes Setting
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        text = "Meta Mensual de Minutos",
                        color = Color(0xFFE2E8F0),
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        IconButton(
                            onClick = { if (monthlyMinutes >= 100) monthlyMinutes -= 100 },
                            modifier = Modifier
                                .size(40.dp)
                                .clip(CircleShape)
                                .background(Color(0xFF1E2538))
                        ) {
                            Icon(Icons.Default.Remove, contentDescription = "-100 min", tint = Color.White)
                        }

                        Text(
                            text = "$monthlyMinutes min",
                            color = Color(0xFF38BDF8),
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Black
                        )

                        IconButton(
                            onClick = { monthlyMinutes += 100 },
                            modifier = Modifier
                                .size(40.dp)
                                .clip(CircleShape)
                                .background(Color(0xFF1E2538))
                        ) {
                            Icon(Icons.Default.Add, contentDescription = "+100 min", tint = Color.White)
                        }
                    }

                    // Presets pills
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        listOf(500, 1000, 1500, 2000).forEach { preset ->
                            Box(
                                modifier = Modifier
                                    .weight(1f)
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(if (monthlyMinutes == preset) Color(0x3338BDF8) else Color(0xFF1A1F33))
                                    .border(
                                        1.dp,
                                        if (monthlyMinutes == preset) Color(0xFF38BDF8) else Color(0x22252C48),
                                        RoundedCornerShape(8.dp)
                                    )
                                    .clickable { monthlyMinutes = preset }
                                    .padding(vertical = 6.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = "$preset m",
                                    color = if (monthlyMinutes == preset) Color(0xFF38BDF8) else Color(0xFF94A3B8),
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.SemiBold
                                )
                            }
                        }
                    }
                }

                // Action Buttons
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    OutlinedButton(
                        onClick = onDismiss,
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF94A3B8))
                    ) {
                        Text("Cancelar")
                    }

                    Button(
                        onClick = {
                            onSaveGoals(yearlyBooks, monthlyMinutes)
                            onDismiss()
                        },
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981))
                    ) {
                        Text("Guardar", color = Color.White, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}

/**
 * Detailed Modal Dialog for an Obsidian Milestone.
 */
@Composable
fun MilestoneDetailDialog(
    milestone: ReadingMilestone,
    onDismiss: () -> Unit
) {
    Dialog(onDismissRequest = onDismiss) {
        Card(
            shape = RoundedCornerShape(24.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF111422)),
            modifier = Modifier
                .fillMaxWidth()
                .border(
                    1.dp,
                    if (milestone.isUnlocked) Color(0xFFFBBF24).copy(alpha = 0.7f) else Color(0xFF2D323F),
                    RoundedCornerShape(24.dp)
                )
                .padding(4.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Trophy / Icon
                Box(
                    modifier = Modifier
                        .size(72.dp)
                        .clip(CircleShape)
                        .background(
                            if (milestone.isUnlocked)
                                Brush.radialGradient(listOf(Color(0x66FBBF24), Color(0x11FBBF24)))
                            else
                                Brush.radialGradient(listOf(Color(0xFF252C48), Color(0xFF131726)))
                        )
                        .border(
                            2.dp,
                            if (milestone.isUnlocked) Color(0xFFFBBF24) else Color(0xFF334155),
                            CircleShape
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = milestone.iconEmoji,
                        fontSize = 36.sp
                    )
                }

                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = milestone.title,
                        color = Color.White,
                        fontSize = 19.sp,
                        fontWeight = FontWeight.Black,
                        textAlign = TextAlign.Center
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = milestone.tierName,
                        color = if (milestone.isUnlocked) Color(0xFFFBBF24) else Color(0xFF94A3B8),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                }

                // Description
                Text(
                    text = milestone.description,
                    color = Color(0xFFCBD5E1),
                    fontSize = 13.sp,
                    textAlign = TextAlign.Center,
                    lineHeight = 18.sp
                )

                // Status Badge & Progress
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(12.dp))
                        .background(Color(0xFF14192A))
                        .border(1.dp, Color(0x33252C48), RoundedCornerShape(12.dp))
                        .padding(14.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                text = "ESTADO DEL HITO",
                                color = Color(0xFF64748B),
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold,
                                letterSpacing = 1.sp
                            )
                            Text(
                                text = if (milestone.isUnlocked) "¡Hito Conquistado!" else "En Proceso",
                                color = if (milestone.isUnlocked) Color(0xFF10B981) else Color(0xFF94A3B8),
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }

                        Text(
                            text = milestone.progressLabel,
                            color = if (milestone.isUnlocked) Color(0xFFFBBF24) else Color.White,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Black
                        )
                    }
                }

                Button(
                    onClick = onDismiss,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (milestone.isUnlocked) Color(0xFFFBBF24) else Color(0xFF1E2538)
                    )
                ) {
                    Text(
                        text = if (milestone.isUnlocked) "¡Magnífico!" else "Entendido",
                        color = if (milestone.isUnlocked) Color(0xFF0D0E11) else Color.White,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}
