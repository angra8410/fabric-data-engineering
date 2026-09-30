package com.universalreadingtracker.presentation.library

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.widget.Toast
import androidx.compose.ui.platform.LocalContext
import com.universalreadingtracker.domain.model.Book
import com.universalreadingtracker.domain.model.ProgressUnit
import com.universalreadingtracker.domain.model.ReadingSession
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

enum class LibrarySubTab(val title: String, val emoji: String) {
    READING("Leyendo", "📖"),
    TO_READ("Por Leer", "⏳"),
    COMPLETED("Completados", "✅"),
    NOTES("Citas & Notas", "💡")
}

/**
 * Implements RF-06, RF-17 & Opción 4:
 * Dedicated Library Management Screen with:
 * - Real-time search by title, author, or quote text
 * - Tabbed segmentation: Leyendo (Reading), Por Leer (Want to read), Completados (Finished), Citas & Notas (Highlights & Notes)
 * - 1-tap Markdown export to clipboard for Obsidian / Notion
 * - Visual progress indicators and Obsidian Luxury book cards
 */
@Composable
fun LibraryScreen(
    books: List<Book>,
    activeBookId: Long,
    notesSessions: List<ReadingSession> = emptyList(),
    onSelectBook: (Long) -> Unit,
    onOpenAddBook: () -> Unit,
    onOpenAddHighlight: () -> Unit = {},
    onOpenUpdatePosition: (Book) -> Unit,
    onMarkAsCompleted: (Book) -> Unit = {},
    onReopenBook: (Book) -> Unit = {},
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var searchQuery by remember { mutableStateOf("") }
    var selectedTab by remember { mutableStateOf(LibrarySubTab.READING) }

    // Segment books into categories:
    // Completed: Books where currentPosition reached or exceeded totalUnits
    val completedBooks = books.filter { it.totalUnits > 0 && it.currentPosition >= it.totalUnits }
    // Reading: Books currently active or in-progress (< totalUnits)
    val readingBooks = books.filter {
        (it.totalUnits <= 0 || it.currentPosition < it.totalUnits) &&
                (it.isCurrentlyReading || it.currentPosition > 0)
    }
    // To Read: Books not yet started and not active
    val toReadBooks = books.filter {
        (it.totalUnits <= 0 || it.currentPosition < it.totalUnits) &&
                it.currentPosition == 0 && !it.isCurrentlyReading
    }
    // Highlights & Notes from reading sessions
    val highlightSessions = notesSessions.filter { !it.notes.isNullOrBlank() }

    val currentList = when (selectedTab) {
        LibrarySubTab.READING -> readingBooks
        LibrarySubTab.TO_READ -> toReadBooks
        LibrarySubTab.COMPLETED -> completedBooks
        LibrarySubTab.NOTES -> emptyList()
    }

    // Apply search filter to books
    val filteredList = currentList.filter {
        searchQuery.isBlank() ||
                it.title.contains(searchQuery, ignoreCase = true) ||
                it.author.contains(searchQuery, ignoreCase = true)
    }

    // Apply search filter to quotes/notes
    val filteredHighlights = highlightSessions.filter {
        searchQuery.isBlank() ||
                it.bookTitle.contains(searchQuery, ignoreCase = true) ||
                it.bookAuthor.contains(searchQuery, ignoreCase = true) ||
                (it.notes ?: "").contains(searchQuery, ignoreCase = true)
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = 18.dp)
    ) {
        Spacer(modifier = Modifier.height(12.dp))

        // Search Bar
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(16.dp))
                .background(Color(0xFF131625))
                .border(1.dp, Color(0x332D323F), RoundedCornerShape(16.dp))
                .padding(horizontal = 14.dp, vertical = 4.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(
                    imageVector = Icons.Default.Search,
                    contentDescription = "Buscar",
                    tint = Color(0xFF94A3B8),
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                TextField(
                    value = searchQuery,
                    onValueChange = { searchQuery = it },
                    placeholder = {
                        Text(
                            text = if (selectedTab == LibrarySubTab.NOTES) "Buscar citas, ideas o libros..." else "Buscar por título o autor...",
                            color = Color(0xFF64748B),
                            fontSize = 14.sp
                        )
                    },
                    colors = TextFieldDefaults.colors(
                        focusedContainerColor = Color.Transparent,
                        unfocusedContainerColor = Color.Transparent,
                        disabledContainerColor = Color.Transparent,
                        focusedIndicatorColor = Color.Transparent,
                        unfocusedIndicatorColor = Color.Transparent,
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White
                    ),
                    singleLine = true,
                    modifier = Modifier.weight(1f)
                )
                if (searchQuery.isNotEmpty()) {
                    IconButton(
                        onClick = { searchQuery = "" },
                        modifier = Modifier.size(24.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Close,
                            contentDescription = "Limpiar",
                            tint = Color(0xFF94A3B8),
                            modifier = Modifier.size(16.dp)
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // SubTab Selector (Leyendo / Por Leer / Completados / Citas & Notas)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(Color(0xFF0F121E))
                .padding(3.dp),
            horizontalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            LibrarySubTab.values().forEach { tab ->
                val isSelected = selectedTab == tab
                val count = when (tab) {
                    LibrarySubTab.READING -> readingBooks.size
                    LibrarySubTab.TO_READ -> toReadBooks.size
                    LibrarySubTab.COMPLETED -> completedBooks.size
                    LibrarySubTab.NOTES -> highlightSessions.size
                }

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
                        Spacer(modifier = Modifier.width(3.dp))
                        Text(
                            text = if (tab == LibrarySubTab.NOTES) "Citas ($count)" else "${tab.title} ($count)",
                            color = if (isSelected) Color.White else Color(0xFF94A3B8),
                            fontSize = 10.sp,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // Header with count & Add button
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = if (selectedTab == LibrarySubTab.NOTES) "${filteredHighlights.size} citas encontradas" else "${filteredList.size} libros encontrados",
                color = Color(0xFF94A3B8),
                fontSize = 12.sp,
                fontWeight = FontWeight.Medium
            )

            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(12.dp))
                    .background(if (selectedTab == LibrarySubTab.NOTES) Color(0x22FBBF24) else Color(0x22FF5E36))
                    .border(
                        1.dp,
                        if (selectedTab == LibrarySubTab.NOTES) Color(0x55FBBF24) else Color(0x55FF5E36),
                        RoundedCornerShape(12.dp)
                    )
                    .clickable {
                        if (selectedTab == LibrarySubTab.NOTES) onOpenAddHighlight() else onOpenAddBook()
                    }
                    .padding(horizontal = 10.dp, vertical = 6.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Default.Add,
                        contentDescription = if (selectedTab == LibrarySubTab.NOTES) "Nueva cita" else "Nuevo libro",
                        tint = if (selectedTab == LibrarySubTab.NOTES) Color(0xFFFBBF24) else Color(0xFFFF774C),
                        modifier = Modifier.size(14.dp)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = if (selectedTab == LibrarySubTab.NOTES) "Nueva Cita" else "Agregar Libro",
                        color = if (selectedTab == LibrarySubTab.NOTES) Color(0xFFFBBF24) else Color(0xFFFF774C),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        // Content List (Books OR Quotes/Highlights)
        if (selectedTab == LibrarySubTab.NOTES) {
            if (filteredHighlights.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(
                            imageVector = Icons.Default.FormatQuote,
                            contentDescription = "Sin citas",
                            tint = Color(0xFF475569),
                            modifier = Modifier.size(44.dp)
                        )
                        Spacer(modifier = Modifier.height(10.dp))
                        Text(
                            text = if (searchQuery.isNotEmpty()) "No se encontraron citas para \"$searchQuery\""
                            else "Aún no tienes citas o reflexiones guardadas.\nToca '+ Nueva Cita' o abre una sesión para capturar una.",
                            color = Color(0xFF64748B),
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Medium,
                            textAlign = androidx.compose.ui.text.style.TextAlign.Center
                        )
                    }
                }
            } else {
                LazyColumn(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                    contentPadding = PaddingValues(bottom = 24.dp)
                ) {
                    items(filteredHighlights, key = { it.id }) { session ->
                        ObsidianQuoteCard(
                            session = session,
                            onCopyMarkdown = {
                                val quoteText = session.notes ?: ""
                                val bookTitle = session.bookTitle.ifBlank { "Lectura en Kindle" }
                                val author = session.bookAuthor.ifBlank { "Autor" }
                                val pageInfo = if (session.endPage != null && session.endPage > 0) " (pág. ${session.endPage})" else ""
                                val md = "> \"$quoteText\"\n— *$bookTitle*, $author$pageInfo\n*Universal Reading Tracker*"
                                val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                                val clip = ClipData.newPlainText("Cita de Lectura", md)
                                clipboard.setPrimaryClip(clip)
                                Toast.makeText(context, "Cita copiada en Markdown para Obsidian / Notion", Toast.LENGTH_SHORT).show()
                            }
                        )
                    }
                }
            }
        } else {
            // Books List
            if (filteredList.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.MenuBook,
                            contentDescription = "Sin libros",
                            tint = Color(0xFF475569),
                            modifier = Modifier.size(44.dp)
                        )
                        Spacer(modifier = Modifier.height(10.dp))
                        Text(
                            text = if (searchQuery.isNotEmpty()) "No se encontraron libros para \"$searchQuery\""
                            else "No tienes libros en la categoría ${selectedTab.title.lowercase()}",
                            color = Color(0xFF64748B),
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
            } else {
                LazyColumn(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                    contentPadding = PaddingValues(bottom = 24.dp)
                ) {
                    items(filteredList, key = { it.id }) { book ->
                        LibraryBookCard(
                            book = book,
                            isActive = book.id == activeBookId,
                            onSelect = { onSelectBook(book.id) },
                            onUpdatePosition = { onOpenUpdatePosition(book) },
                            onMarkAsCompleted = { onMarkAsCompleted(book) },
                            onReopenBook = { onReopenBook(book) }
                        )
                    }
                }
            }
        }
    }
}

/**
 * Individual Obsidian Luxury Card for a Quote/Highlight with 1-tap Markdown copy for Obsidian/Notion.
 */
@Composable
fun ObsidianQuoteCard(
    session: ReadingSession,
    onCopyMarkdown: () -> Unit,
    modifier: Modifier = Modifier
) {
    val zone = ZoneId.systemDefault()
    val dateFormatter = DateTimeFormatter.ofPattern("d 'de' MMMM, yyyy", Locale.forLanguageTag("es-ES"))
    val dateStr = if (session.startTime > 0) {
        Instant.ofEpochMilli(session.startTime).atZone(zone).toLocalDate().format(dateFormatter)
    } else "Sesión de lectura"

    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Color(0xFF131522))
            .border(1.dp, Color(0x332D323F), RoundedCornerShape(16.dp))
            .padding(14.dp)
    ) {
        Column {
            // Header: Book info & Page
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Row(modifier = Modifier.weight(1f), verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(34.dp)
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0x22FBBF24)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.FormatQuote,
                            contentDescription = "Cita",
                            tint = Color(0xFFFBBF24),
                            modifier = Modifier.size(18.dp)
                        )
                    }
                    Spacer(modifier = Modifier.width(10.dp))
                    Column {
                        Text(
                            text = session.bookTitle.ifBlank { "Lectura en Kindle" },
                            color = Color.White,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold,
                            maxLines = 1
                        )
                        Text(
                            text = session.bookAuthor.ifBlank { "Autor" },
                            color = Color(0xFF94A3B8),
                            fontSize = 11.sp,
                            maxLines = 1
                        )
                    }
                }

                if (session.endPage != null && session.endPage > 0) {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(6.dp))
                            .background(Color(0xFF1E293B))
                            .padding(horizontal = 6.dp, vertical = 3.dp)
                    ) {
                        Text(
                            text = "Pág. ${session.endPage}",
                            color = Color(0xFF38BDF8),
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Blockquote container
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(8.dp))
                    .background(Color(0xFF181B2B))
                    .border(
                        width = 2.dp,
                        color = Color(0xFFFBBF24),
                        shape = RoundedCornerShape(topStart = 8.dp, bottomStart = 8.dp)
                    )
                    .padding(horizontal = 12.dp, vertical = 10.dp)
            ) {
                Text(
                    text = "“${session.notes ?: ""}”",
                    color = Color(0xFFF1F5F9),
                    fontSize = 13.sp,
                    fontStyle = androidx.compose.ui.text.font.FontStyle.Italic,
                    lineHeight = 18.sp
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Footer: Date & 1-tap Copy Markdown Button
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "📅 $dateStr",
                    color = Color(0xFF64748B),
                    fontSize = 11.sp
                )

                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color(0x2238BDF8))
                        .border(1.dp, Color(0x4438BDF8), RoundedCornerShape(8.dp))
                        .clickable { onCopyMarkdown() }
                        .padding(horizontal = 10.dp, vertical = 5.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.ContentCopy,
                            contentDescription = "Copiar Markdown",
                            tint = Color(0xFF38BDF8),
                            modifier = Modifier.size(12.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = "Copiar Markdown",
                            color = Color(0xFF38BDF8),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
}

/**
 * Individual Obsidian Luxury Card for a Book in the Library.
 */
@Composable
fun LibraryBookCard(
    book: Book,
    isActive: Boolean,
    onSelect: () -> Unit,
    onUpdatePosition: () -> Unit,
    onMarkAsCompleted: () -> Unit,
    onReopenBook: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Color(0xFF131522))
            .border(
                width = if (isActive) 1.5.dp else 1.dp,
                color = if (isActive) Color(0xFFFBBF24) else Color(0x332D323F),
                shape = RoundedCornerShape(16.dp)
            )
            .clickable { onSelect() }
            .padding(14.dp)
    ) {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Book Icon Badge
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .clip(RoundedCornerShape(10.dp))
                        .background(if (isActive) Color(0x33FBBF24) else Color(0x2238BDF8)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.MenuBook,
                        contentDescription = "Libro",
                        tint = if (isActive) Color(0xFFFBBF24) else Color(0xFF38BDF8),
                        modifier = Modifier.size(20.dp)
                    )
                }

                Spacer(modifier = Modifier.width(12.dp))

                // Title & Author
                Column(modifier = Modifier.weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = book.title,
                            color = Color.White,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold,
                            maxLines = 1,
                            modifier = Modifier.weight(1f, fill = false)
                        )
                        if (isActive) {
                            Spacer(modifier = Modifier.width(6.dp))
                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .background(Color(0x33FBBF24))
                                    .padding(horizontal = 6.dp, vertical = 2.dp)
                            ) {
                                Text(
                                    text = "ACTIVO",
                                    color = Color(0xFFFBBF24),
                                    fontSize = 9.sp,
                                    fontWeight = FontWeight.Black
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(2.dp))

                    Text(
                        text = book.author,
                        color = Color(0xFF94A3B8),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium,
                        maxLines = 1
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Progress Bar
            val pct = book.progressPercentage
            Column {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = "${book.unitLabel} ${book.currentPosition} de ${book.totalUnits}",
                        color = Color(0xFFCBD5E1),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                    Text(
                        text = "$pct%",
                        color = if (pct >= 100) Color(0xFF10B981) else Color(0xFFFBBF24),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                Spacer(modifier = Modifier.height(4.dp))

                LinearProgressIndicator(
                    progress = { (pct / 100f).coerceIn(0f, 1f) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(6.dp)
                        .clip(RoundedCornerShape(3.dp)),
                    color = if (pct >= 100) Color(0xFF10B981) else Color(0xFFFBBF24),
                    trackColor = Color(0xFF1F2333)
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Actions row: Set Active / Update Page / Mark Completed / Reopen
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Left action: Status / Completed Badge OR "Marcar Leído" Button
                if (pct >= 100) {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0x2210B981))
                            .border(1.dp, Color(0x4410B981), RoundedCornerShape(8.dp))
                            .padding(horizontal = 8.dp, vertical = 5.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.CheckCircle,
                                contentDescription = null,
                                tint = Color(0xFF34D399),
                                modifier = Modifier.size(13.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                text = "Completado",
                                color = Color(0xFF34D399),
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                } else {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0x1A10B981))
                            .border(1.dp, Color(0x4410B981), RoundedCornerShape(8.dp))
                            .clickable { onMarkAsCompleted() }
                            .padding(horizontal = 9.dp, vertical = 5.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.CheckCircle,
                                contentDescription = "Marcar como leído",
                                tint = Color(0xFF34D399),
                                modifier = Modifier.size(13.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                text = "Marcar Leído",
                                color = Color(0xFF34D399),
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }

                // Right actions: Reopen, Avanzar/Páginas, Leer Ahora
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    if (pct >= 100) {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(8.dp))
                                .background(Color(0x1A38BDF8))
                                .border(1.dp, Color(0x3338BDF8), RoundedCornerShape(8.dp))
                            .clickable { onReopenBook() }
                            .padding(horizontal = 9.dp, vertical = 5.dp)
                        ) {
                            Text(
                                text = "Reabrir",
                                color = Color(0xFF38BDF8),
                                fontSize = 11.sp,
                                fontWeight = FontWeight.SemiBold
                            )
                        }
                    }

                    // Update position button
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0x1AFFFFFF))
                            .clickable { onUpdatePosition() }
                            .padding(horizontal = 9.dp, vertical = 5.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.Edit,
                                contentDescription = "Editar página",
                                tint = Color(0xFFCBD5E1),
                                modifier = Modifier.size(12.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                text = if (pct >= 100) "Páginas" else "Avanzar",
                                color = Color(0xFFCBD5E1),
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }

                    if (!isActive && pct < 100) {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(8.dp))
                                .background(Color(0x2210B981))
                                .border(1.dp, Color(0x4410B981), RoundedCornerShape(8.dp))
                                .clickable { onSelect() }
                                .padding(horizontal = 10.dp, vertical = 5.dp)
                        ) {
                            Text(
                                text = "Leer Ahora",
                                color = Color(0xFF34D399),
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }
        }
    }
}

