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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
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
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.universalreadingtracker.domain.model.Book
import com.universalreadingtracker.domain.model.DailyReadingSummary
import com.universalreadingtracker.domain.model.ProgressUnit
import com.universalreadingtracker.domain.model.ReadingModality
import com.universalreadingtracker.domain.model.ReadingSession
import com.universalreadingtracker.presentation.dashboard.analytics.AnalyticsScreen
import com.universalreadingtracker.presentation.library.LibraryScreen
import com.universalreadingtracker.presentation.navigation.AppTab
import com.universalreadingtracker.presentation.navigation.LuxuryBottomNavigation

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

/**
 * Strips diacritics/tildes and converts to lowercase for fast, robust fuzzy searching.
 * Example: "Hábitos" -> "habitos", "Kahneman" -> "kahneman".
 */
fun normalizeForSearch(text: String): String {
    return java.text.Normalizer.normalize(text, java.text.Normalizer.Form.NFD)
        .replace("\\p{InCombiningDiacriticalMarks}+".toRegex(), "")
        .lowercase()
        .trim()
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    state: DashboardState,
    onToggleKindleTimer: () -> Unit,
    onSelectBook: (Long) -> Unit = {},
    onAddNewBook: (String, String, ProgressUnit, Int, Int) -> Unit = { _, _, _, _, _ -> },
    onUpdatePosition: (Int) -> Unit = {},
    onUpdateBookPosition: (Long, Int) -> Unit = { _, _ -> },
    onExportJson: () -> Unit = {},
    onSyncCatalog: () -> Unit = {}
) {
    var currentTab by remember { mutableStateOf(AppTab.HOME) }
    var showNfcDialog by remember { mutableStateOf(false) }
    var showBookSelectorDialog by remember { mutableStateOf(false) }
    var showAddBookDialog by remember { mutableStateOf(false) }
    var showUpdatePositionDialog by remember { mutableStateOf(false) }
    var bookToUpdatePosition by remember { mutableStateOf<Book?>(null) }
    var selectedSessionForDetails by remember { mutableStateOf<ReadingSession?>(null) }

    // Dialogs
    if (showNfcDialog) {
        NfcSetupDialog(onDismiss = { showNfcDialog = false })
    }

    if (showBookSelectorDialog) {
        BookSelectorDialog(
            books = state.activeBooks,
            activeBookId = state.activeBook?.id ?: 0,
            onSelect = { bookId ->
                onSelectBook(bookId)
                showBookSelectorDialog = false
            },
            onOpenAddBook = {
                showBookSelectorDialog = false
                showAddBookDialog = true
            },
            onSyncCatalog = onSyncCatalog,
            onDismiss = { showBookSelectorDialog = false }
        )
    }

    if (showAddBookDialog) {
        AddBookDialog(
            onSave = { title, author, unit, curPos, total ->
                onAddNewBook(title, author, unit, curPos, total)
                showAddBookDialog = false
            },
            onDismiss = { showAddBookDialog = false }
        )
    }

    val targetBook = bookToUpdatePosition ?: state.activeBook
    if (showUpdatePositionDialog && targetBook != null) {
        UpdatePositionDialog(
            book = targetBook,
            onSave = { newPos ->
                onUpdateBookPosition(targetBook.id, newPos)
                bookToUpdatePosition = null
                showUpdatePositionDialog = false
            },
            onDismiss = {
                bookToUpdatePosition = null
                showUpdatePositionDialog = false
            }
        )
    }

    if (selectedSessionForDetails != null) {
        val session = selectedSessionForDetails!!
        SessionDetailDialog(
            session = session,
            streakDays = state.streakInfo.currentStreakDays,
            dailyGoalMinutes = state.dailyGoalMinutes,
            onContinueReading = {
                val targetBookId = if (session.bookId > 0) {
                    session.bookId
                } else {
                    state.activeBooks.find { it.title.equals(session.bookTitle, ignoreCase = true) }?.id
                }
                if (targetBookId != null && targetBookId > 0) {
                    onSelectBook(targetBookId)
                }
                selectedSessionForDetails = null
            },
            onDismiss = { selectedSessionForDetails = null }
        )
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

                            Row(verticalAlignment = Alignment.CenterVertically) {
                                // JSON Export Action Button
                                Box(
                                    modifier = Modifier
                                        .clip(RoundedCornerShape(20.dp))
                                        .background(Color(0x2238BDF8))
                                        .border(1.dp, Color(0x5538BDF8), RoundedCornerShape(20.dp))
                                        .clickable { onExportJson() }
                                        .padding(horizontal = 9.dp, vertical = 5.dp),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Icon(
                                            imageVector = Icons.Default.FileDownload,
                                            contentDescription = "Exportar JSON",
                                            tint = Color(0xFF38BDF8),
                                            modifier = Modifier.size(13.dp)
                                        )
                                        Spacer(modifier = Modifier.width(4.dp))
                                        Text(
                                            text = "JSON",
                                            color = Color(0xFF38BDF8),
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Bold
                                        )
                                    }
                                }

                                Spacer(modifier = Modifier.width(8.dp))

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
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent)
                )
            },
            bottomBar = {
                LuxuryBottomNavigation(
                    currentTab = currentTab,
                    onTabSelected = { currentTab = it }
                )
            }
        ) { innerPadding ->
            AnimatedContent(
                targetState = currentTab,
                transitionSpec = { fadeIn(tween(250)) togetherWith fadeOut(tween(200)) },
                label = "MainTabTransition",
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
            ) { tab ->
                when (tab) {
                    AppTab.HOME -> {
                        LazyColumn(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(horizontal = 18.dp),
                            verticalArrangement = Arrangement.spacedBy(16.dp),
                            contentPadding = PaddingValues(bottom = 16.dp)
                        ) {
                            // 1. Hero Obsidian Trophy Card (Racha Consolidada)
                            item {
                                LuxuryStreakCard(
                                    streakDays = state.streakInfo.currentStreakDays,
                                    longestStreak = state.streakInfo.longestStreakDays,
                                    isStreakActiveToday = state.streakInfo.isStreakActiveToday,
                                    dailySummaries = state.allDailySummaries
                                )
                            }

                            // 2. Active Kindle Book Card with Dropdown Selector & Pág / Loc Tracking
                            item {
                                ActiveBookGlassCard(
                                    books = state.activeBooks,
                                    book = state.activeBook,
                                    onSelectBook = onSelectBook,
                                    onOpenBookSelector = { showBookSelectorDialog = true },
                                    onOpenUpdatePosition = { showUpdatePositionDialog = true },
                                    onSyncCatalog = onSyncCatalog
                                )
                            }

                            // 3. Hardware & Providers Grid (Audible & Kindle)
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
                                        onToggle = {
                                            val wasRunning = state.isKindleTimerRunning
                                            onToggleKindleTimer()
                                            if (wasRunning) {
                                                showUpdatePositionDialog = true
                                            }
                                        }
                                    )
                                }
                            }

                            // 4. NFC Smart Tap Pill
                            item {
                                NfcMagicPill(onOpenSetup = { showNfcDialog = true })
                            }

                            // 5. Today's Dual-Progress Display
                            item {
                                TodayProgressGlassCard(
                                    todayMinutes = state.todaySummary?.totalMinutesRead ?: 0,
                                    goalMinutes = state.dailyGoalMinutes,
                                    audioMinutes = state.todaySummary?.audioMinutes ?: 0,
                                    kindleMinutes = state.todaySummary?.kindleMinutes ?: 0
                                )
                            }

                            // 6. Historial Reciente Header
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

                            // 7. Recent Sessions List
                            if (state.recentSessions.isEmpty()) {
                                item {
                                    EmptyHistoryCard()
                                }
                            } else {
                                items(state.recentSessions) { session ->
                                    LuxurySessionRow(
                                        session = session,
                                        onClick = { selectedSessionForDetails = session }
                                    )
                                }
                            }

                            item {
                                Spacer(modifier = Modifier.height(16.dp))
                            }
                        }
                    }
                    AppTab.ANALYTICS -> {
                        AnalyticsScreen(
                            analytics = state.analytics,
                            currentStreakDays = state.streakInfo.currentStreakDays,
                            activeBook = state.activeBook
                        )
                    }
                    AppTab.LIBRARY -> {
                        LibraryScreen(
                            books = state.activeBooks,
                            activeBookId = state.activeBook?.id ?: 0,
                            onSelectBook = onSelectBook,
                            onOpenAddBook = { showAddBookDialog = true },
                            onOpenUpdatePosition = { book ->
                                bookToUpdatePosition = book
                                showUpdatePositionDialog = true
                            }
                        )
                    }
                }
            }
        }
    }
}

/**
 * Active Book Card on Kindle: Displays current title, progress in Pág or Loc, and quick update buttons.
 */
/**
 * Active Book Card on Kindle: Features 1-tap access to the searchable book library
 * with fuzzy search and full scrolling, displays current position/progress in Pág or Loc,
 * and quick update buttons.
 */
@Composable
fun ActiveBookGlassCard(
    books: List<Book>,
    book: Book?,
    onSelectBook: (Long) -> Unit,
    onOpenBookSelector: () -> Unit,
    onOpenUpdatePosition: () -> Unit,
    onSyncCatalog: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(22.dp))
            .border(1.dp, GlowCyanBorder, RoundedCornerShape(22.dp)),
        colors = CardDefaults.cardColors(containerColor = SurfaceGlass)
    ) {
        Column(modifier = Modifier.padding(18.dp)) {
            // Header with LEYENDO EN KINDLE and Searchable List Trigger
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    modifier = Modifier
                        .weight(1f)
                        .clip(RoundedCornerShape(8.dp))
                        .clickable { onOpenBookSelector() },
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .size(34.dp)
                            .clip(RoundedCornerShape(10.dp))
                            .background(Brush.linearGradient(ElectricCyanGradient)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.MenuBook,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(18.dp)
                        )
                    }
                    Spacer(modifier = Modifier.width(10.dp))
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .padding(vertical = 2.dp)
                    ) {
                        Text(
                            text = "LEYENDO EN KINDLE",
                            color = Color(0xFF38BDF8),
                            fontSize = 10.sp,
                            fontWeight = FontWeight.ExtraBold,
                            letterSpacing = 1.2.sp
                        )
                        Row(
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = book?.title ?: "Elegir de la lista...",
                                color = Color.White,
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Bold,
                                maxLines = 1,
                                modifier = Modifier.weight(1f, fill = false)
                            )
                            Icon(
                                imageVector = Icons.Default.ArrowDropDown,
                                contentDescription = "Abrir lista de libros",
                                tint = Color(0xFF00E5FF),
                                modifier = Modifier.size(24.dp)
                            )
                        }
                    }
                }

                // Searchable List Pill Button
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(12.dp))
                        .background(Color(0x2238BDF8))
                        .border(1.dp, Color(0x4438BDF8), RoundedCornerShape(12.dp))
                        .clickable { onOpenBookSelector() }
                        .padding(horizontal = 10.dp, vertical = 5.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.Search,
                            contentDescription = null,
                            tint = Color(0xFF7DD3FC),
                            modifier = Modifier.size(13.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = "Buscar",
                            color = Color(0xFF7DD3FC),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Icon(
                            imageVector = Icons.Default.ArrowDropDown,
                            contentDescription = null,
                            tint = Color(0xFF7DD3FC),
                            modifier = Modifier.size(15.dp)
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            if (book != null) {
                // Progress details row
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = book.author,
                        color = Color(0xFF94A3B8),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium
                    )

                    // Unit & Position Pill
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0x1A00E5FF))
                            .padding(horizontal = 8.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = book.formattedProgress,
                            color = Color(0xFF00E5FF),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))

                // Progress Bar
                val progressFraction = (book.progressPercentage.toFloat() / 100f).coerceIn(0f, 1f)
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(6.dp)
                        .clip(RoundedCornerShape(3.dp))
                        .background(Color(0xFF1E2438))
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth(progressFraction)
                            .fillMaxHeight()
                            .clip(RoundedCornerShape(3.dp))
                            .background(Brush.horizontalGradient(ElectricCyanGradient))
                    )
                }

                Spacer(modifier = Modifier.height(12.dp))

                // Quick Update Button
                Button(
                    onClick = onOpenUpdatePosition,
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF1E293B)),
                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(34.dp)
                        .border(1.dp, GlassBorderStroke, RoundedCornerShape(12.dp))
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.Edit,
                            contentDescription = null,
                            tint = Color(0xFF38BDF8),
                            modifier = Modifier.size(14.dp)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Actualizar ${book.unitLabel} actual",
                            color = Color(0xFFE2E8F0),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            } else {
                Button(
                    onClick = onOpenBookSelector,
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0284C7)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Seleccionar libro de la lista", color = Color.White, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

/**
 * Searchable Book Picker Dialog with real-time fuzzy search by title or author,
 * unlimited smooth scrolling (LazyColumn), and instant 1-tap book activation.
 */
@Composable
fun BookSelectorDialog(
    books: List<Book>,
    activeBookId: Long,
    onSelect: (Long) -> Unit,
    onOpenAddBook: () -> Unit,
    onSyncCatalog: () -> Unit = {},
    onDismiss: () -> Unit
) {
    var searchQuery by remember { mutableStateOf("") }

    val filteredBooks = remember(books, searchQuery) {
        if (searchQuery.isBlank()) {
            books
        } else {
            val normQuery = normalizeForSearch(searchQuery)
            val tokens = normQuery.split(" ").filter { it.isNotBlank() }
            books.filter { book ->
                val normTitle = normalizeForSearch(book.title)
                val normAuthor = normalizeForSearch(book.author)
                tokens.all { token -> normTitle.contains(token) || normAuthor.contains(token) }
            }
        }
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = Color(0xFF131522),
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(max = 680.dp),
        title = {
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
                            .background(Brush.linearGradient(ElectricCyanGradient)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.MenuBook,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                    Spacer(modifier = Modifier.width(8.dp))
                    Column {
                        Text(
                            text = "Biblioteca Kindle",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 17.sp
                        )
                        Text(
                            text = "${filteredBooks.size} de ${books.size} libros",
                            color = Color(0xFF38BDF8),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
                Row {
                    IconButton(onClick = onSyncCatalog) {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = "Sincronizar catálogo",
                            tint = Color(0xFF38BDF8)
                        )
                    }
                    IconButton(onClick = onOpenAddBook) {
                        Icon(
                            imageVector = Icons.Default.Add,
                            contentDescription = "Añadir libro",
                            tint = Color(0xFF00E5FF)
                        )
                    }
                }
            }
        },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 2.dp)
            ) {
                // Search Input with Instant Fuzzy Filter
                OutlinedTextField(
                    value = searchQuery,
                    onValueChange = { searchQuery = it },
                    placeholder = {
                        Text(
                            text = "Buscar por título o autor...",
                            color = Color(0xFF64748B),
                            fontSize = 13.sp
                        )
                    },
                    leadingIcon = {
                        Icon(
                            imageVector = Icons.Default.Search,
                            contentDescription = "Buscar",
                            tint = Color(0xFF00E5FF),
                            modifier = Modifier.size(18.dp)
                        )
                    },
                    trailingIcon = {
                        if (searchQuery.isNotBlank()) {
                            IconButton(onClick = { searchQuery = "" }) {
                                Icon(
                                    imageVector = Icons.Default.Close,
                                    contentDescription = "Limpiar búsqueda",
                                    tint = Color(0xFF94A3B8),
                                    modifier = Modifier.size(16.dp)
                                )
                            }
                        }
                    },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedBorderColor = Color(0xFF00E5FF),
                        unfocusedBorderColor = Color(0x33FFFFFF),
                        cursorColor = Color(0xFF00E5FF)
                    ),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Scrollable List of Books (LazyColumn)
                if (filteredBooks.isEmpty()) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(140.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Icon(
                                imageVector = Icons.Default.Search,
                                contentDescription = null,
                                tint = Color(0xFF64748B),
                                modifier = Modifier.size(32.dp)
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = if (searchQuery.isNotBlank()) "Sin resultados para \"$searchQuery\"" else "No hay libros guardados",
                                color = Color(0xFF94A3B8),
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }
                } else {
                    LazyColumn(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(max = 380.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        items(filteredBooks, key = { it.id }) { book ->
                            val isSelected = book.id == activeBookId
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clip(RoundedCornerShape(14.dp))
                                    .background(if (isSelected) Color(0x3300E5FF) else Color(0xFF1A1D2E))
                                    .border(
                                        1.dp,
                                        if (isSelected) Color(0xFF00E5FF) else GlassBorderStroke,
                                        RoundedCornerShape(14.dp)
                                    )
                                    .clickable {
                                        onSelect(book.id)
                                    }
                                    .padding(horizontal = 14.dp, vertical = 10.dp)
                            ) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text(
                                            text = book.title,
                                            color = if (isSelected) Color(0xFF00E5FF) else Color.White,
                                            fontSize = 14.sp,
                                            fontWeight = if (isSelected) FontWeight.ExtraBold else FontWeight.Bold
                                        )
                                        Spacer(modifier = Modifier.height(2.dp))
                                        Text(
                                            text = "${book.author} · ${book.formattedProgress}",
                                            color = Color(0xFF94A3B8),
                                            fontSize = 11.sp
                                        )
                                    }
                                    if (isSelected) {
                                        Icon(
                                            imageVector = Icons.Default.CheckCircle,
                                            contentDescription = "Activo",
                                            tint = Color(0xFF00E5FF),
                                            modifier = Modifier.size(20.dp)
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            Button(
                onClick = onOpenAddBook,
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0284C7)),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("+ Añadir Otro", color = Color.White, fontWeight = FontWeight.Bold)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cerrar", color = Color(0xFF94A3B8))
            }
        }
    )
}

/**
 * Dialog to add a new book with choice of Pages or Kindle Location (Loc).
 */
@Composable
fun AddBookDialog(
    onSave: (title: String, author: String, unit: ProgressUnit, curPos: Int, totalUnits: Int) -> Unit,
    onDismiss: () -> Unit
) {
    var title by remember { mutableStateOf("") }
    var author by remember { mutableStateOf("") }
    var unit by remember { mutableStateOf(ProgressUnit.PAGES) }
    var currentPosStr by remember { mutableStateOf("0") }
    var totalUnitsStr by remember { mutableStateOf("300") }

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = Color(0xFF131522),
        title = {
            Text(
                text = "Añadir Libro para Kindle",
                color = Color.White,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp
            )
        },
        text = {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                OutlinedTextField(
                    value = title,
                    onValueChange = { title = it },
                    label = { Text("Título del libro") },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedBorderColor = Color(0xFF00E5FF)
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = author,
                    onValueChange = { author = it },
                    label = { Text("Autor") },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedBorderColor = Color(0xFF00E5FF)
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                Text(
                    text = "¿Cómo mide el avance tu Kindle?",
                    color = Color(0xFF94A3B8),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold
                )

                // Segmented Selector: Páginas vs Loc
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(12.dp))
                        .background(Color(0xFF1A1D2E))
                        .padding(4.dp),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(10.dp))
                            .background(if (unit == ProgressUnit.PAGES) Color(0xFF0284C7) else Color.Transparent)
                            .clickable { unit = ProgressUnit.PAGES }
                            .padding(vertical = 8.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "Páginas (pág)",
                            color = if (unit == ProgressUnit.PAGES) Color.White else Color(0xFF94A3B8),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }

                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(10.dp))
                            .background(if (unit == ProgressUnit.LOCATIONS) Color(0xFF7C3AED) else Color.Transparent)
                            .clickable { unit = ProgressUnit.LOCATIONS }
                            .padding(vertical = 8.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "Posición (Loc)",
                            color = if (unit == ProgressUnit.LOCATIONS) Color.White else Color(0xFF94A3B8),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    OutlinedTextField(
                        value = currentPosStr,
                        onValueChange = { currentPosStr = it },
                        label = { Text(if (unit == ProgressUnit.PAGES) "Pág actual" else "Loc actual") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White,
                            focusedBorderColor = Color(0xFF00E5FF)
                        ),
                        modifier = Modifier.weight(1f)
                    )

                    OutlinedTextField(
                        value = totalUnitsStr,
                        onValueChange = { totalUnitsStr = it },
                        label = { Text(if (unit == ProgressUnit.PAGES) "Total págs" else "Total Locs") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White,
                            focusedBorderColor = Color(0xFF00E5FF)
                        ),
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    if (title.isNotBlank()) {
                        val cur = currentPosStr.toIntOrNull() ?: 0
                        val tot = totalUnitsStr.toIntOrNull() ?: 0
                        onSave(title, author, unit, cur, tot)
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0284C7)),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("Guardar y Activar", color = Color.White, fontWeight = FontWeight.Bold)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancelar", color = Color(0xFF94A3B8))
            }
        }
    )
}

/**
 * Fast dialog to update Kindle position (Pages or Loc).
 */
@Composable
fun UpdatePositionDialog(
    book: Book,
    onSave: (Int) -> Unit,
    onDismiss: () -> Unit
) {
    var positionStr by remember { mutableStateOf(book.currentPosition.toString()) }

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = Color(0xFF131522),
        title = {
            Text(
                text = "Actualizar ${book.unitLabel}",
                color = Color.White,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp
            )
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text(
                    text = "${book.title} (${book.author})",
                    color = Color(0xFF38BDF8),
                    fontSize = 13.sp,
                    fontWeight = FontWeight.SemiBold
                )

                OutlinedTextField(
                    value = positionStr,
                    onValueChange = { positionStr = it },
                    label = { Text("Nueva posición (${book.unitLabel})") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedBorderColor = Color(0xFF00E5FF)
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                // Quick Increment Chips
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    val currentVal = positionStr.toIntOrNull() ?: book.currentPosition
                    listOf(1, 5, 10, 25).forEach { delta ->
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .clip(RoundedCornerShape(8.dp))
                                .background(Color(0xFF1E293B))
                                .border(1.dp, GlassBorderStroke, RoundedCornerShape(8.dp))
                                .clickable {
                                    val next = (currentVal + delta)
                                    positionStr = next.toString()
                                }
                                .padding(vertical = 6.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "+$delta",
                                color = Color(0xFFE2E8F0),
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    val parsed = positionStr.toIntOrNull() ?: book.currentPosition
                    onSave(parsed)
                },
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0284C7)),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("Guardar", color = Color.White, fontWeight = FontWeight.Bold)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Omitir", color = Color(0xFF94A3B8))
            }
        }
    )
}

/**
 * 1. Hero Luxury Trophy Streak Card.
 * Deep obsidian glass surface with dynamic warm aura, pulsating 3D flame badge, and weekly dots.
 */
@Composable
fun LuxuryStreakCard(
    streakDays: Int,
    longestStreak: Int,
    isStreakActiveToday: Boolean = false,
    dailySummaries: List<DailyReadingSummary> = emptyList()
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

                // Weekly consistency dots capsule (L M M J V S D for CURRENT WEEK)
                val today = java.time.LocalDate.now()
                val mondayOfCurrentWeek = today.with(java.time.temporal.TemporalAdjusters.previousOrSame(java.time.DayOfWeek.MONDAY))
                val summaryByDate = remember(dailySummaries) {
                    dailySummaries.associateBy { it.date }
                }

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
                        val dayDate = mondayOfCurrentWeek.plusDays(index.toLong())
                        val isToday = dayDate.isEqual(today)
                        val isFuture = dayDate.isAfter(today)

                        val dayDateStr = dayDate.format(java.time.format.DateTimeFormatter.ISO_LOCAL_DATE)
                        val summary = summaryByDate[dayDateStr]

                        val isCompleted = when {
                            isFuture -> false // Days ahead in the current week are deactivated
                            isToday -> isStreakActiveToday || summary?.isValidStreakDay == true
                            else -> summary?.isValidStreakDay == true // Past days in this week
                        }

                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                text = day,
                                color = when {
                                    isCompleted -> Color(0xFFF1F5F9)
                                    isToday -> Color(0xFFFF9900)
                                    else -> Color(0xFF475569) // Deactivated / future day color
                                },
                                fontSize = 10.sp,
                                fontWeight = if (isToday || isCompleted) FontWeight.ExtraBold else FontWeight.Medium
                            )
                            Spacer(modifier = Modifier.height(5.dp))
                            Box(
                                modifier = Modifier
                                    .size(18.dp)
                                    .clip(CircleShape)
                                    .background(
                                        when {
                                            isCompleted -> Brush.linearGradient(EmberFlameGradient)
                                            isToday -> Brush.linearGradient(listOf(Color(0x44FF9900), Color(0x22FF5722)))
                                            else -> Brush.linearGradient(listOf(Color(0x18FFFFFF), Color(0x0AFFFFFF)))
                                        }
                                    )
                                    .then(
                                        when {
                                            isToday && !isCompleted -> Modifier.border(1.2.dp, GlowAmberBorder, CircleShape)
                                            isFuture -> Modifier.border(1.dp, Color(0x1EFFFFFF), CircleShape)
                                            else -> Modifier
                                        }
                                    ),
                                contentAlignment = Alignment.Center
                            ) {
                                if (isCompleted) {
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

                Spacer(modifier = Modifier.height(10.dp))
                Row(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color(0x18FFFFFF))
                        .padding(horizontal = 8.dp, vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(text = "🔔", fontSize = 11.sp)
                    Spacer(modifier = Modifier.width(5.dp))
                    Text(
                        text = "Alerta de racha activa: 9:00 PM (Colombia) si no has leído",
                        color = Color(0xFFCBD5E1),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium
                    )
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
 * 6. Luxury Session Row with stylized typography, format badge, and interactive detail trigger.
 */
@Composable
fun LuxurySessionRow(
    session: ReadingSession,
    onClick: () -> Unit = {}
) {
    val isAudio = session.modality == ReadingModality.AUDIOBOOK
    val icon = if (isAudio) Icons.Default.Headphones else Icons.AutoMirrored.Filled.MenuBook
    val gradient = if (isAudio) AudibleAmberGradient else ElectricCyanGradient

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(18.dp))
            .border(1.dp, GlassBorderStroke, RoundedCornerShape(18.dp))
            .clickable { onClick() },
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
                    fontWeight = FontWeight.Bold,
                    maxLines = 1,
                    overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = session.bookAuthor.ifBlank { session.providerId.uppercase() },
                    color = Color(0xFF94A3B8),
                    fontSize = 12.sp,
                    maxLines = 1,
                    overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis
                )
            }

            Spacer(modifier = Modifier.width(8.dp))

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

            Spacer(modifier = Modifier.width(8.dp))

            Icon(
                imageVector = Icons.Default.ChevronRight,
                contentDescription = "Ver métricas",
                tint = Color(0xFF64748B),
                modifier = Modifier.size(18.dp)
            )
        }
    }
}

/**
 * Interactive Session Detail Dialog: Displays comprehensive reading metrics,
 * duration, exact time range, reading speed (pages/hr), modality badge, and quick actions.
 */
@Composable
fun SessionDetailDialog(
    session: ReadingSession,
    streakDays: Int,
    dailyGoalMinutes: Int,
    onContinueReading: () -> Unit,
    onDismiss: () -> Unit
) {
    val isAudio = session.modality == ReadingModality.AUDIOBOOK
    val icon = if (isAudio) Icons.Default.Headphones else Icons.AutoMirrored.Filled.MenuBook
    val gradient = if (isAudio) AudibleAmberGradient else ElectricCyanGradient
    val glowColor = if (isAudio) GlowAmberBorder else GlowCyanBorder

    val zone = java.time.ZoneId.systemDefault()
    val timeFormatter = java.time.format.DateTimeFormatter.ofPattern("hh:mm a", java.util.Locale.getDefault())
    val dateFormatter = java.time.format.DateTimeFormatter.ofPattern("EEEE, d 'de' MMMM", java.util.Locale.forLanguageTag("es-ES"))

    val effectiveStart = if (session.startTime > 0) session.startTime else (System.currentTimeMillis() - session.realDurationSeconds * 1000)
    val effectiveEnd = if (session.endTime > 0) session.endTime else System.currentTimeMillis()

    val startInstant = java.time.Instant.ofEpochMilli(effectiveStart)
    val endInstant = java.time.Instant.ofEpochMilli(effectiveEnd)

    val startTimeStr = startInstant.atZone(zone).format(timeFormatter)
    val endTimeStr = endInstant.atZone(zone).format(timeFormatter)
    val dateStr = startInstant.atZone(zone).toLocalDate().format(dateFormatter).replaceFirstChar { it.uppercase() }

    val readingSpeedPph = if (session.pagesRead != null && session.pagesRead > 0 && session.durationMinutes > 0) {
        String.format(java.util.Locale.US, "%.1f", (session.pagesRead.toFloat() / session.durationMinutes) * 60)
    } else null

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = Color(0xFF131522),
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 4.dp),
        title = {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(36.dp)
                            .clip(RoundedCornerShape(10.dp))
                            .background(Brush.linearGradient(gradient)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = icon,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(18.dp)
                        )
                    }
                    Spacer(modifier = Modifier.width(10.dp))
                    Column {
                        Text(
                            text = "FICHA DE SESIÓN",
                            color = if (isAudio) Color(0xFFFFB300) else Color(0xFF38BDF8),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.ExtraBold,
                            letterSpacing = 1.2.sp
                        )
                        Text(
                            text = "Métricas de Lectura",
                            color = Color.White,
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                IconButton(onClick = onDismiss) {
                    Icon(imageVector = Icons.Default.Close, contentDescription = "Cerrar", tint = Color(0xFF94A3B8))
                }
            }
        },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                // 1. Hero Book Banner
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(18.dp))
                        .background(Color(0xFF1A1D2E))
                        .border(1.dp, glowColor, RoundedCornerShape(18.dp))
                        .padding(16.dp)
                ) {
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .background(if (isAudio) Color(0x33FFB300) else Color(0x3300E5FF))
                                    .padding(horizontal = 8.dp, vertical = 3.dp)
                            ) {
                                Text(
                                    text = if (isAudio) "🎧 AUDIOLIBRO" else "📖 KINDLE FÍSICO",
                                    color = if (isAudio) Color(0xFFFFB300) else Color(0xFF00E5FF),
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Black,
                                    letterSpacing = 0.8.sp
                                )
                            }
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = session.bookTitle.ifBlank { "Lectura en Kindle" },
                            color = Color.White,
                            fontSize = 18.sp,
                            fontWeight = FontWeight.ExtraBold,
                            lineHeight = 22.sp
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = session.bookAuthor.ifBlank { session.providerId.uppercase() },
                            color = Color(0xFF94A3B8),
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }

                // 2. Grid de 4 Métricas Clave
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    MetricCard(
                        modifier = Modifier.weight(1f),
                        icon = Icons.Default.Timer,
                        iconColor = Color(0xFFFF9900),
                        label = "Tiempo Neto",
                        value = "${session.durationMinutes} min",
                        subtitle = "${session.realDurationSeconds}s reloj real"
                    )

                    MetricCard(
                        modifier = Modifier.weight(1f),
                        icon = Icons.Default.Schedule,
                        iconColor = Color(0xFF38BDF8),
                        label = "Horario",
                        value = startTimeStr,
                        subtitle = "Hasta $endTimeStr"
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    MetricCard(
                        modifier = Modifier.weight(1f),
                        icon = Icons.Default.Speed,
                        iconColor = Color(0xFFA855F7),
                        label = "Ritmo Lector",
                        value = if (session.pagesRead != null && session.pagesRead > 0) "+${session.pagesRead} págs" else "Continuo",
                        subtitle = if (readingSpeedPph != null) "$readingSpeedPph págs/h" else "${session.durationMinutes} min inmersión"
                    )

                    MetricCard(
                        modifier = Modifier.weight(1f),
                        icon = Icons.Default.EmojiEvents,
                        iconColor = Color(0xFF10B981),
                        label = "Aporte de Racha",
                        value = "+${session.durationMinutes} min",
                        subtitle = "Racha de $streakDays d 🔥"
                    )
                }

                // 3. Tarjeta de Fecha & Páginas
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(14.dp))
                        .background(Color(0x1A000000))
                        .border(1.dp, GlassBorderStroke, RoundedCornerShape(14.dp))
                        .padding(horizontal = 14.dp, vertical = 10.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(text = "📅", fontSize = 14.sp)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = dateStr,
                                color = Color(0xFFE2E8F0),
                                fontSize = 12.sp,
                                fontWeight = FontWeight.SemiBold
                            )
                        }
                        if (session.startPage != null && session.endPage != null && session.endPage >= session.startPage) {
                            Text(
                                text = "Pág. ${session.startPage} ➔ ${session.endPage}",
                                color = Color(0xFF38BDF8),
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            Button(
                onClick = onContinueReading,
                colors = ButtonDefaults.buttonColors(containerColor = Color.Transparent),
                contentPadding = PaddingValues(),
                shape = RoundedCornerShape(14.dp)
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Brush.linearGradient(ElectricCyanGradient), RoundedCornerShape(14.dp))
                        .padding(vertical = 12.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.MenuBook,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Continuar leyendo este libro",
                            color = Color.White,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text(text = "Cerrar", color = Color(0xFF94A3B8), fontWeight = FontWeight.SemiBold)
            }
        }
    )
}

@Composable
fun MetricCard(
    modifier: Modifier = Modifier,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    iconColor: Color,
    label: String,
    value: String,
    subtitle: String
) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(14.dp))
            .background(Color(0xFF161928))
            .border(1.dp, GlassBorderStroke, RoundedCornerShape(14.dp))
            .padding(12.dp)
    ) {
        Column {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = iconColor,
                    modifier = Modifier.size(14.dp)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = label,
                    color = Color(0xFF94A3B8),
                    fontSize = 11.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = value,
                color = Color.White,
                fontSize = 15.sp,
                fontWeight = FontWeight.Black
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = subtitle,
                color = Color(0xFF64748B),
                fontSize = 10.sp,
                fontWeight = FontWeight.Medium,
                maxLines = 1,
                overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis
            )
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
                text = "Historial de 164+ días listo en memoria",
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
