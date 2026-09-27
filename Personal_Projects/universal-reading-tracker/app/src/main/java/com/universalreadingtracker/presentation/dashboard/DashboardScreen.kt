package com.universalreadingtracker.presentation.dashboard

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.MenuBook
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.universalreadingtracker.domain.model.ReadingModality
import com.universalreadingtracker.domain.model.ReadingSession

// ==========================================
// PALETA DE DISEÑO: OBSIDIAN LUXURY SYSTEM
// ==========================================
val DarkCanvas = Color(0xFF07080C)
val SurfaceGlass = Color(0xFF11131E)
val SurfaceElevated = Color(0xFF161928)
val GlassBorderStroke = Color(0x24FFFFFF)
val GlowAmberBorder = Color(0x66FF7700)
val GlowCyanBorder = Color(0x6600E5FF)
val GlowPurpleBorder = Color(0x66A855F7)

val EmberFlameGradient = listOf(Color(0xFFFFB300), Color(0xFFFF5722), Color(0xFFFF1744))
val ElectricCyanGradient = listOf(Color(0xFF00E5FF), Color(0xFF0072FF))
val AudibleAmberGradient = listOf(Color(0xFFFFC107), Color(0xFFFF6D00))
val NfcVioletGradient = listOf(Color(0xFFA855F7), Color(0xFF6366F1))

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    state: DashboardState,
    onToggleKindleTimer: () -> Unit
) {
    var showNfcDialog by remember { mutableStateOf(false) }

    if (showNfcDialog) {
        NfcSetupDialog(onDismiss = { showNfcDialog = false })
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.radialGradient(
                    colors = listOf(Color(0xFF13172E), DarkCanvas),
                    center = Offset(400f, 150f),
                    radius = 900f
                )
            )
    ) {
        Scaffold(
            containerColor = Color.Transparent,
            topBar = {
                TopAppBar(
                    title = {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween,
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(end = 12.dp)
                        ) {
                            Column {
                                Text(
                                    text = "MI HÁBITO LECTOR",
                                    color = Color(0xFF94A3B8),
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    letterSpacing = 2.sp
                                )
                                Text(
                                    text = "Universal Tracker",
                                    color = Color.White,
                                    fontSize = 22.sp,
                                    fontWeight = FontWeight.Black,
                                    letterSpacing = 0.5.sp
                                )
                            }
                            // Elite consistency chip
                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(20.dp))
                                    .background(Color(0x1A10B981))
                                    .border(1.dp, Color(0x4410B981), RoundedCornerShape(20.dp))
                                    .padding(horizontal = 10.dp, vertical = 5.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Box(
                                        modifier = Modifier
                                            .size(7.dp)
                                            .clip(CircleShape)
                                            .background(Color(0xFF10B981))
                                    )
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text(
                                        text = "Top 0.1%",
                                        color = Color(0xFF34D399),
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Bold
                                    )
                                }
                            }
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent)
                )
            }
        ) { innerPadding ->
            val screenVisibleState = remember { MutableTransitionState(false).apply { targetState = true } }
            AnimatedVisibility(
                visibleState = screenVisibleState,
                enter = androidx.compose.animation.fadeIn(animationSpec = tween(400)) +
                        androidx.compose.animation.slideInVertically(
                            animationSpec = tween(500, easing = FastOutSlowInEasing),
                            initialOffsetY = { 70 }
                        )
            ) {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(innerPadding)
                        .padding(horizontal = 18.dp),
                    verticalArrangement = Arrangement.spacedBy(18.dp)
                ) {
                    // 1. Hero Obsidian Trophy Card (Racha 163 Días)
                    item {
                        LuxuryStreakCard(
                            streakDays = state.streakInfo.currentStreakDays,
                            longestStreak = state.streakInfo.longestStreakDays,
                            isStreakActiveToday = state.streakInfo.isStreakActiveToday
                        )
                    }

                // 2. Hardware & Providers Grid (Audible & Kindle)
                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Dispositivos & Hábitos",
                            color = Color(0xFFE2E8F0),
                            fontSize = 15.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .size(6.dp)
                                    .clip(CircleShape)
                                    .background(Color(0xFF34D399))
                            )
                            Spacer(modifier = Modifier.width(5.dp))
                            Text(
                                text = "En tiempo real",
                                color = Color(0xFF94A3B8),
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }
                    Spacer(modifier = Modifier.height(10.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        AudibleLuxuryCard(
                            modifier = Modifier.weight(1f),
                            isActive = state.isAudibleTrackingActive
                        )
                        KindleLuxuryCard(
                            modifier = Modifier.weight(1f),
                            isRunning = state.isKindleTimerRunning,
                            onToggle = onToggleKindleTimer
                        )
                    }
                }

                // 3. NFC Smart Tap Pill
                item {
                    NfcMagicPill(onOpenSetup = { showNfcDialog = true })
                }

                // 4. Today's Dual-Progress Display
                item {
                    TodayProgressGlassCard(
                        todayMinutes = state.todaySummary?.totalMinutesRead ?: 0,
                        goalMinutes = state.dailyGoalMinutes,
                        audioMinutes = state.todaySummary?.audioMinutes ?: 0,
                        kindleMinutes = state.todaySummary?.kindleMinutes ?: 0
                    )
                }

                // 5. Historial Reciente Header
                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Historial Reciente",
                            color = Color(0xFFE2E8F0),
                            fontSize = 15.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "Ver todo",
                            color = Color(0xFF38BDF8),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                }

                // 6. Recent Sessions List
                if (state.recentSessions.isEmpty()) {
                    item {
                        EmptyHistoryCard()
                    }
                } else {
                    items(state.recentSessions) { session ->
                        LuxurySessionRow(session = session)
                    }
                }

                    item {
                        Spacer(modifier = Modifier.height(28.dp))
                    }
                }
            }
        }
    }
}

/**
 * 1. Hero Luxury Trophy Streak Card.
 * Deep obsidian glass surface with dynamic warm aura, pulsating 3D flame badge, and weekly dots.
 */
@Composable
fun LuxuryStreakCard(
    streakDays: Int,
    longestStreak: Int,
    isStreakActiveToday: Boolean = false
) {
    val infiniteTransition = rememberInfiniteTransition(label = "flame_pulse")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 0.95f,
        targetValue = 1.08f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse_scale"
    )
    val auraAlpha by infiniteTransition.animateFloat(
        initialValue = 0.25f,
        targetValue = 0.55f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "aura_alpha"
    )

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .shadow(20.dp, RoundedCornerShape(26.dp), spotColor = Color(0x66FF5722)),
        shape = RoundedCornerShape(26.dp),
        colors = CardDefaults.cardColors(containerColor = SurfaceGlass)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            Color(0xFF3B151E),
                            Color(0xFF181524),
                            Color(0xFF0F1019)
                        ),
                        center = Offset(750f, 150f),
                        radius = 800f
                    )
                )
                .border(
                    width = 1.dp,
                    brush = Brush.linearGradient(
                        listOf(GlowAmberBorder, GlassBorderStroke)
                    ),
                    shape = RoundedCornerShape(26.dp)
                )
                .padding(22.dp)
        ) {
            Column {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = "⚡ RACHA HISTÓRICA ACTIVA",
                                color = Color(0xFFF97316),
                                fontSize = 11.sp,
                                fontWeight = FontWeight.ExtraBold,
                                letterSpacing = 1.2.sp
                            )
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Row(verticalAlignment = Alignment.Bottom) {
                            Text(
                                text = "$streakDays",
                                color = Color.White,
                                fontSize = 52.sp,
                                fontWeight = FontWeight.Black,
                                lineHeight = 52.sp
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "DÍAS",
                                color = Color(0xFFFF9900),
                                fontSize = 18.sp,
                                fontWeight = FontWeight.Black,
                                modifier = Modifier.padding(bottom = 6.dp)
                            )
                        }
                    }

                    // Pulsing Flame Icon with Breathing Aura
                    Box(
                        modifier = Modifier.size(70.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        // Outer glowing aura halo
                        Box(
                            modifier = Modifier
                                .size(64.dp)
                                .scale(pulseScale * 1.15f)
                                .clip(CircleShape)
                                .background(Color(0xFFFF5722).copy(alpha = auraAlpha * 0.4f))
                        )
                        // Flame button
                        Box(
                            modifier = Modifier
                                .scale(pulseScale)
                                .size(54.dp)
                                .clip(CircleShape)
                                .background(Brush.linearGradient(EmberFlameGradient))
                                .border(1.5.dp, Color.White.copy(alpha = 0.5f), CircleShape),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(text = "🔥", fontSize = 28.sp)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Weekly consistency dots capsule (L M M J V S D)
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(16.dp))
                        .background(Color(0x26000000))
                        .border(1.dp, GlassBorderStroke, RoundedCornerShape(16.dp))
                        .padding(horizontal = 14.dp, vertical = 10.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    val daysOfWeek = listOf("L", "M", "M", "J", "V", "S", "D")
                    daysOfWeek.forEachIndexed { index, day ->
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                text = day,
                                color = if (index <= 5) Color(0xFFF1F5F9) else Color(0xFF64748B),
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(modifier = Modifier.height(5.dp))
                            Box(
                                modifier = Modifier
                                    .size(18.dp)
                                    .clip(CircleShape)
                                    .background(
                                        if (index <= 5) Brush.linearGradient(EmberFlameGradient)
                                        else Brush.linearGradient(listOf(Color(0x33FFFFFF), Color(0x11FFFFFF)))
                                    ),
                                contentAlignment = Alignment.Center
                            ) {
                                if (index <= 5) {
                                    Icon(
                                        imageVector = Icons.Default.Check,
                                        contentDescription = null,
                                        tint = Color.White,
                                        modifier = Modifier.size(12.dp)
                                    )
                                }
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(12.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    if (isStreakActiveToday) {
                        Text(
                            text = "🏆 ¡Racha de $streakDays días blindada hoy!",
                            color = Color(0xFFFDE047),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Mañana alcanzará ${streakDays + 1}.",
                            color = Color(0xFF94A3B8),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Medium
                        )
                    } else {
                        Text(
                            text = "⚡ Racha de $streakDays días activa.",
                            color = Color(0xFFFF9900),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Lee hoy para extenderla a ${streakDays + 1}.",
                            color = Color(0xFF94A3B8),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
            }
        }
    }
}

/**
 * 2. Audible Luxury Card with harmonic animated soundwave equalizer.
 * Mathematically balanced with Kindle card height (172.dp).
 */
@Composable
fun AudibleLuxuryCard(modifier: Modifier, isActive: Boolean) {
    Card(
        modifier = modifier
            .height(172.dp)
            .clip(RoundedCornerShape(22.dp))
            .border(1.dp, if (isActive) GlowAmberBorder else GlassBorderStroke, RoundedCornerShape(22.dp)),
        colors = CardDefaults.cardColors(containerColor = SurfaceGlass)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(38.dp)
                        .clip(RoundedCornerShape(12.dp))
                        .background(Brush.linearGradient(AudibleAmberGradient)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.Headphones,
                        contentDescription = "Audible",
                        tint = Color.White,
                        modifier = Modifier.size(20.dp)
                    )
                }

                // Live harmonic animated soundwave
                if (isActive) {
                    AudioSoundBars()
                } else {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0x1A64748B))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = "PASIVO",
                            color = Color(0xFF94A3B8),
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }

            Column {
                Text(
                    text = "Audible",
                    color = Color.White,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "Audiobook automático",
                    color = Color(0xFF94A3B8),
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Medium
                )
            }

            // Bottom Status Capsule
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(10.dp))
                    .background(
                        if (isActive) Color(0x2210B981) else Color(0x1A334155)
                    )
                    .border(
                        1.dp,
                        if (isActive) Color(0x4410B981) else Color(0x22475569),
                        RoundedCornerShape(10.dp)
                    )
                    .padding(vertical = 6.dp),
                contentAlignment = Alignment.Center
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(6.dp)
                            .clip(CircleShape)
                            .background(if (isActive) Color(0xFF10B981) else Color(0xFF64748B))
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = if (isActive) "Escuchando en vivo" else "Detección 2° plano",
                        color = if (isActive) Color(0xFF34D399) else Color(0xFF94A3B8),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        }
    }
}

@Composable
fun AudioSoundBars() {
    val transition = rememberInfiniteTransition(label = "audio_harmonic")
    val bar1 by transition.animateFloat(
        initialValue = 4f, targetValue = 18f,
        animationSpec = infiniteRepeatable(tween(420, easing = LinearEasing), RepeatMode.Reverse),
        label = "b1"
    )
    val bar2 by transition.animateFloat(
        initialValue = 16f, targetValue = 6f,
        animationSpec = infiniteRepeatable(tween(360, easing = LinearEasing), RepeatMode.Reverse),
        label = "b2"
    )
    val bar3 by transition.animateFloat(
        initialValue = 8f, targetValue = 20f,
        animationSpec = infiniteRepeatable(tween(480, easing = LinearEasing), RepeatMode.Reverse),
        label = "b3"
    )
    val bar4 by transition.animateFloat(
        initialValue = 14f, targetValue = 5f,
        animationSpec = infiniteRepeatable(tween(390, easing = LinearEasing), RepeatMode.Reverse),
        label = "b4"
    )

    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(2.5.dp),
        modifier = Modifier.height(20.dp)
    ) {
        Box(modifier = Modifier.width(3.dp).height(bar1.dp).clip(RoundedCornerShape(2.dp)).background(Color(0xFFFFB300)))
        Box(modifier = Modifier.width(3.dp).height(bar2.dp).clip(RoundedCornerShape(2.dp)).background(Color(0xFFFF7043)))
        Box(modifier = Modifier.width(3.dp).height(bar3.dp).clip(RoundedCornerShape(2.dp)).background(Color(0xFFFF5252)))
        Box(modifier = Modifier.width(3.dp).height(bar4.dp).clip(RoundedCornerShape(2.dp)).background(Color(0xFFFFB300)))
    }
}

/**
 * 3. Kindle Luxury Card with vibrant Cyan glow and responsive tactile button.
 * Mathematically balanced with Audible card height (172.dp).
 */
@Composable
fun KindleLuxuryCard(
    modifier: Modifier,
    isRunning: Boolean,
    onToggle: () -> Unit
) {
    val haptic = LocalHapticFeedback.current

    Card(
        modifier = modifier
            .height(172.dp)
            .clip(RoundedCornerShape(22.dp))
            .border(
                1.dp,
                if (isRunning) GlowCyanBorder else GlassBorderStroke,
                RoundedCornerShape(22.dp)
            ),
        colors = CardDefaults.cardColors(containerColor = SurfaceGlass)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(38.dp)
                        .clip(RoundedCornerShape(12.dp))
                        .background(Brush.linearGradient(ElectricCyanGradient)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.MenuBook,
                        contentDescription = "Kindle",
                        tint = Color.White,
                        modifier = Modifier.size(20.dp)
                    )
                }

                if (isRunning) {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0x3300E5FF))
                            .border(1.dp, Color(0x6600E5FF), RoundedCornerShape(8.dp))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = "EN CURSO",
                            color = Color(0xFF00E5FF),
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Black
                        )
                    }
                } else {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0x1A64748B))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = "HARDWARE",
                            color = Color(0xFF94A3B8),
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }

            Column {
                Text(
                    text = "Kindle Físico",
                    color = Color.White,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = if (isRunning) "Registrando lectura..." else "E-reader / Papel",
                    color = if (isRunning) Color(0xFF38BDF8) else Color(0xFF94A3B8),
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Medium
                )
            }

            // Interactive glowing button with tactile response
            Button(
                onClick = {
                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                    onToggle()
                },
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (isRunning) Color(0xFFDC2626) else Color(0xFF0284C7)
                ),
                contentPadding = PaddingValues(horizontal = 10.dp, vertical = 6.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(36.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = if (isRunning) Icons.Default.Stop else Icons.Default.PlayArrow,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = if (isRunning) "Detener" else "Iniciar",
                        color = Color.White,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.ExtraBold
                    )
                }
            }
        }
    }
}

/**
 * 4. NFC Magic Pill (Compact luxury touchpoint with proper flex and single-line button).
 */
@Composable
fun NfcMagicPill(onOpenSetup: () -> Unit) {
    val haptic = LocalHapticFeedback.current

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .background(
                Brush.horizontalGradient(
                    listOf(
                        Color(0xFF2E1065).copy(alpha = 0.5f),
                        Color(0xFF1E1B4B).copy(alpha = 0.35f)
                    )
                )
            )
            .border(1.dp, GlowPurpleBorder, RoundedCornerShape(20.dp))
            .clickable(
                interactionSource = remember { MutableInteractionSource() },
                indication = null
            ) {
                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                onOpenSetup()
            }
            .padding(horizontal = 14.dp, vertical = 12.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(
                modifier = Modifier.weight(1f),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(38.dp)
                        .clip(CircleShape)
                        .background(Brush.linearGradient(NfcVioletGradient)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.Nfc,
                        contentDescription = "NFC",
                        tint = Color.White,
                        modifier = Modifier.size(20.dp)
                    )
                }
                Spacer(modifier = Modifier.width(12.dp))
                Column {
                    Text(
                        text = "Sticker NFC para Kindle",
                        color = Color.White,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "Toca la funda para iniciar o parar",
                        color = Color(0xFFC084FC),
                        fontSize = 11.sp,
                        maxLines = 1
                    )
                }
            }

            Spacer(modifier = Modifier.width(8.dp))

            // Action chip with guaranteed single line
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(12.dp))
                    .background(Color(0xFF7C3AED).copy(alpha = 0.3f))
                    .border(1.dp, Color(0xFFA855F7).copy(alpha = 0.5f), RoundedCornerShape(12.dp))
                    .padding(horizontal = 12.dp, vertical = 6.dp)
            ) {
                Text(
                    text = "Vincular",
                    color = Color(0xFFE9D5FF),
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    maxLines = 1
                )
            }
        }
    }
}

/**
 * 5. Today's Progress Card with smooth spring animated bar and split statistics.
 */
@Composable
fun TodayProgressGlassCard(
    todayMinutes: Int,
    goalMinutes: Int,
    audioMinutes: Int,
    kindleMinutes: Int
) {
    val targetProgress = (todayMinutes.toFloat() / maxOf(1, goalMinutes).toFloat()).coerceIn(0f, 1f)
    val animatedProgress by animateFloatAsState(
        targetValue = targetProgress,
        animationSpec = spring(
            dampingRatio = Spring.DampingRatioLowBouncy,
            stiffness = Spring.StiffnessLow
        ),
        label = "progress_anim"
    )

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(22.dp))
            .border(1.dp, GlassBorderStroke, RoundedCornerShape(22.dp)),
        colors = CardDefaults.cardColors(containerColor = SurfaceGlass)
    ) {
        Column(modifier = Modifier.padding(18.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "META DE HOY",
                        color = Color(0xFF94A3B8),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = "$todayMinutes de $goalMinutes min",
                        color = Color.White,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Black
                    )
                }

                // Dynamic Completion / Progress Pill
                val isCompleted = todayMinutes >= goalMinutes
                val hasStarted = todayMinutes > 0
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(16.dp))
                        .background(
                            when {
                                isCompleted -> Color(0x2210B981)
                                hasStarted -> Color(0x220284C7)
                                else -> Color(0x1A64748B)
                            }
                        )
                        .border(
                            1.dp,
                            when {
                                isCompleted -> Color(0x5510B981)
                                hasStarted -> Color(0x550284C7)
                                else -> Color(0x2264748B)
                            },
                            RoundedCornerShape(16.dp)
                        )
                        .padding(horizontal = 10.dp, vertical = 4.dp)
                ) {
                    val pillText = when {
                        isCompleted -> "¡Meta Cumplida! 🎯"
                        hasStarted -> "${((todayMinutes.toFloat() / goalMinutes) * 100).toInt()}% en curso"
                        else -> "Por comenzar 📖"
                    }
                    val pillColor = when {
                        isCompleted -> Color(0xFF34D399)
                        hasStarted -> Color(0xFF38BDF8)
                        else -> Color(0xFF94A3B8)
                    }
                    Text(
                        text = pillText,
                        color = pillColor,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Smooth Multi-Color Progress Track
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(10.dp)
                    .clip(RoundedCornerShape(5.dp))
                    .background(Color(0xFF1E2438))
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth(animatedProgress)
                        .fillMaxHeight()
                        .clip(RoundedCornerShape(5.dp))
                        .background(
                            Brush.horizontalGradient(
                                listOf(Color(0xFFFFB300), Color(0xFF00E5FF))
                            )
                        )
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Chips with category details
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(8.dp).clip(CircleShape).background(Color(0xFFFFB300)))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "Audible: $audioMinutes min",
                        color = Color(0xFFCBD5E1),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(8.dp).clip(CircleShape).background(Color(0xFF00E5FF)))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "Kindle: $kindleMinutes min",
                        color = Color(0xFFCBD5E1),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }
    }
}

/**
 * 6. Luxury Session Row with stylized typography and format badge.
 */
@Composable
fun LuxurySessionRow(session: ReadingSession) {
    val isAudio = session.modality == ReadingModality.AUDIOBOOK
    val icon = if (isAudio) Icons.Default.Headphones else Icons.AutoMirrored.Filled.MenuBook
    val gradient = if (isAudio) AudibleAmberGradient else ElectricCyanGradient

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(18.dp))
            .border(1.dp, GlassBorderStroke, RoundedCornerShape(18.dp)),
        colors = CardDefaults.cardColors(containerColor = SurfaceGlass)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(44.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(Brush.linearGradient(gradient)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = Color.White,
                    modifier = Modifier.size(22.dp)
                )
            }

            Spacer(modifier = Modifier.width(14.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = session.bookTitle.ifBlank { "Lectura en Kindle" },
                    color = Color.White,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = session.bookAuthor.ifBlank { session.providerId.uppercase() },
                    color = Color(0xFF94A3B8),
                    fontSize = 12.sp
                )
            }

            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = "${session.durationMinutes} min",
                    color = Color.White,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.ExtraBold
                )
                if (session.pagesRead != null && session.pagesRead > 0) {
                    Text(
                        text = "+${session.pagesRead} págs",
                        color = Color(0xFF38BDF8),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        }
    }
}

@Composable
fun EmptyHistoryCard() {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(18.dp))
            .border(1.dp, GlassBorderStroke, RoundedCornerShape(18.dp)),
        colors = CardDefaults.cardColors(containerColor = SurfaceGlass.copy(alpha = 0.5f))
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(text = "📚", fontSize = 34.sp)
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Historial de 163 días listo en memoria",
                color = Color.White,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "Toca 'Iniciar' en Kindle o dale Play a Audible para sumar hoy.",
                color = Color(0xFF94A3B8),
                fontSize = 12.sp
            )
        }
    }
}

@Composable
fun NfcSetupDialog(onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = Color(0xFF131522),
        icon = {
            Box(
                modifier = Modifier
                    .size(54.dp)
                    .clip(CircleShape)
                    .background(Brush.linearGradient(NfcVioletGradient)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Nfc,
                    contentDescription = null,
                    tint = Color.White,
                    modifier = Modifier.size(28.dp)
                )
            }
        },
        title = {
            Text(
                text = "Vincular Sticker NFC para Kindle",
                color = Color.White,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp
            )
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text(
                    text = "1. Pega tu sticker NFC en la funda de tu Kindle físico.",
                    color = Color(0xFFCBD5E1),
                    fontSize = 13.sp
                )
                Text(
                    text = "2. Con esta pantalla abierta, acerca el sticker a la parte trasera de tu teléfono para programarlo en 1 segundo.",
                    color = Color(0xFFCBD5E1),
                    fontSize = 13.sp
                )
                Text(
                    text = "✨ A partir de ese momento, apoyar tu teléfono en el Kindle iniciará tu lectura al instante sin tocar ninguna pantalla.",
                    color = Color(0xFFC084FC),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }
        },
        confirmButton = {
            Button(
                onClick = onDismiss,
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF7C3AED)),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("Listo", color = Color.White, fontWeight = FontWeight.Bold)
            }
        }
    )
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
