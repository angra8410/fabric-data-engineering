package com.universalreadingtracker.presentation.dashboard

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.universalreadingtracker.domain.model.ReadingModality
import com.universalreadingtracker.domain.model.ReadingSession

/**
 * Main Dashboard Screen in Jetpack Compose.
 * Implements RF-05, RF-06, RF-08, ADR-005, ADR-007, ADR-008.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    state: DashboardState,
    onToggleKindleTimer: () -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = "Universal Reading Tracker",
                            fontWeight = FontWeight.Bold,
                            fontSize = 20.sp
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        }
    ) { innerPadding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 1. Streak Hero Card (Honoring the 163 days reading streak)
            item {
                StreakCard(
                    streakDays = state.streakInfo.currentStreakDays,
                    totalDays = state.streakInfo.totalHistoricalDays
                )
            }

            // 2. Multimodal Action Panel (Audible Passive status & Kindle 1-Tap Timer)
            item {
                Text(
                    text = "Control de Proveedores",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold
                )
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // Audible Status Card
                    ProviderStatusCard(
                        modifier = Modifier.weight(1f),
                        providerName = "Audible",
                        statusText = "Detección Pasiva Activa",
                        icon = Icons.Default.Headphones,
                        cardColor = Color(0xFFF9A825),
                        isActive = state.isAudibleTrackingActive
                    )

                    // Kindle Timer Quick Action Card
                    KindleActionCard(
                        modifier = Modifier.weight(1f),
                        isRunning = state.isKindleTimerRunning,
                        onToggle = onToggleKindleTimer
                    )
                }
            }

            // 3. Today's Reading Progress Breakdown
            item {
                TodayProgressCard(
                    todayMinutes = state.todaySummary?.totalMinutesRead ?: 0,
                    goalMinutes = state.dailyGoalMinutes,
                    audioMinutes = state.todaySummary?.audioMinutes ?: 0,
                    kindleMinutes = state.todaySummary?.kindleMinutes ?: 0
                )
            }

            // 4. Recent Sessions Header
            item {
                Text(
                    text = "Sesiones Recientes",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold
                )
            }

            // 5. Recent Sessions List
            if (state.recentSessions.isEmpty()) {
                item {
                    EmptySessionsCard()
                }
            } else {
                items(state.recentSessions) { session ->
                    SessionItemCard(session = session)
                }
            }

            item {
                Spacer(modifier = Modifier.height(24.dp))
            }
        }
    }
}

@Composable
fun StreakCard(streakDays: Int, totalDays: Int) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    Brush.horizontalGradient(
                        colors = listOf(
                            Color(0xFFFF6F00).copy(alpha = 0.85f),
                            Color(0xFFFF8F00).copy(alpha = 0.95f)
                        )
                    )
                )
                .padding(20.dp)
        ) {
            Column {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column {
                        Text(
                            text = "RACHA HISTÓRICA",
                            color = Color.White.copy(alpha = 0.85f),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 1.sp
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "🔥 $streakDays Días",
                            color = Color.White,
                            fontSize = 32.sp,
                            fontWeight = FontWeight.ExtraBold
                        )
                    }
                    Box(
                        modifier = Modifier
                            .size(54.dp)
                            .clip(CircleShape)
                            .background(Color.White.copy(alpha = 0.2f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.LocalFireDepartment,
                            contentDescription = "Racha Activa",
                            tint = Color.White,
                            modifier = Modifier.size(36.dp)
                        )
                    }
                }
                Spacer(modifier = Modifier.height(10.dp))
                Text(
                    text = "¡Increíble consistencia! Tu racha está protegida y continuará a ${streakDays + 1} mañana.",
                    color = Color.White.copy(alpha = 0.95f),
                    fontSize = 13.sp
                )
            }
        }
    }
}

@Composable
fun ProviderStatusCard(
    modifier: Modifier,
    providerName: String,
    statusText: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    cardColor: Color,
    isActive: Boolean
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = icon,
                    contentDescription = providerName,
                    tint = cardColor,
                    modifier = Modifier.size(22.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = providerName,
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .clip(CircleShape)
                        .background(if (isActive) Color(0xFF4CAF50) else Color.Gray)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = if (isActive) "Escuchando" else "Pausado",
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
fun KindleActionCard(
    modifier: Modifier,
    isRunning: Boolean,
    onToggle: () -> Unit
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (isRunning) Color(0xFF1B5E20) else MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Default.MenuBook,
                    contentDescription = "Kindle Físico",
                    tint = if (isRunning) Color.White else Color(0xFF0288D1),
                    modifier = Modifier.size(22.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "Kindle Físico",
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp,
                    color = if (isRunning) Color.White else MaterialTheme.colorScheme.onSurface
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = onToggle,
                shape = RoundedCornerShape(10.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (isRunning) Color(0xFFE53935) else Color(0xFF0288D1)
                ),
                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = if (isRunning) "Finalizar" else "Iniciar Lectura",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }
        }
    }
}

@Composable
fun TodayProgressCard(
    todayMinutes: Int,
    goalMinutes: Int,
    audioMinutes: Int,
    kindleMinutes: Int
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Lectura de Hoy",
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp
                )
                Text(
                    text = "$todayMinutes / $goalMinutes min",
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.primary,
                    fontSize = 14.sp
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            val progress = (todayMinutes.toFloat() / goalMinutes.toFloat()).coerceIn(0f, 1f)
            LinearProgressIndicator(
                progress = progress,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(8.dp)
                    .clip(RoundedCornerShape(4.dp))
            )
            Spacer(modifier = Modifier.height(12.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceAround
            ) {
                Text(
                    text = "🎧 Audible: $audioMinutes min",
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = "📖 Kindle: $kindleMinutes min",
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
fun SessionItemCard(session: ReadingSession) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            val icon = if (session.modality == ReadingModality.AUDIOBOOK) Icons.Default.Headphones else Icons.Default.MenuBook
            val badgeColor = if (session.modality == ReadingModality.AUDIOBOOK) Color(0xFFF9A825) else Color(0xFF0288D1)

            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(badgeColor.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(imageVector = icon, contentDescription = null, tint = badgeColor)
            }
            Spacer(modifier = Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = session.bookTitle.ifBlank { "Sesión de lectura" },
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp
                )
                Text(
                    text = session.bookAuthor.ifBlank { session.providerId },
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = "${session.durationMinutes} min",
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    color = MaterialTheme.colorScheme.primary
                )
                if (session.pagesRead != null && session.pagesRead > 0) {
                    Text(
                        text = "+${session.pagesRead} págs",
                        fontSize = 11.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}

@Composable
fun EmptySessionsCard() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                imageVector = Icons.Default.AutoStories,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.size(36.dp)
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Tu historial de 163 días está sembrado y listo.",
                fontSize = 13.sp,
                fontWeight = FontWeight.Medium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Text(
                text = "Inicia reproducción en Audible o pulsa 'Iniciar Lectura' para tu Kindle.",
                fontSize = 11.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.8f)
            )
        }
    }
}

@androidx.compose.ui.tooling.preview.Preview(showBackground = true, showSystemUi = true)
@Composable
fun DashboardScreenPreview() {
    MaterialTheme {
        DashboardScreen(
            state = DashboardState(
                streakInfo = com.universalreadingtracker.domain.model.StreakInfo(163, 163, true, 163),
                todaySummary = com.universalreadingtracker.domain.model.DailyReadingSummary(
                    date = "2026-09-26",
                    totalMinutesRead = 45,
                    audioMinutes = 30,
                    kindleMinutes = 15,
                    physicalMinutes = 0,
                    goalReached = true,
                    isHistoricalBackfill = false
                ),
                recentSessions = listOf(
                    ReadingSession(
                        id = 1,
                        bookId = 1,
                        bookTitle = "Atomic Habits",
                        bookAuthor = "James Clear",
                        modality = ReadingModality.AUDIOBOOK,
                        providerId = "audible",
                        startTime = System.currentTimeMillis() - 3600000,
                        endTime = System.currentTimeMillis() - 1800000,
                        realDurationSeconds = 1800
                    ),
                    ReadingSession(
                        id = 2,
                        bookId = 2,
                        bookTitle = "Klara and the Sun",
                        bookAuthor = "Kazuo Ishiguro",
                        modality = ReadingModality.EBOOK_KINDLE,
                        providerId = "kindle_physical",
                        startTime = System.currentTimeMillis() - 7200000,
                        endTime = System.currentTimeMillis() - 6300000,
                        realDurationSeconds = 900,
                        startPage = 120,
                        endPage = 138
                    )
                )
            ),
            onToggleKindleTimer = {}
        )
    }
}

