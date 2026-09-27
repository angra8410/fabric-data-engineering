package com.universalreadingtracker.domain.model

/**
 * Domain entity representing a Book in the local catalog.
 * Supports both Page numbers and Kindle Locations (Loc).
 */
data class Book(
    val id: Long = 0,
    val title: String,
    val author: String,
    val format: BookFormat = BookFormat.EBOOK,
    val primaryProviderId: String = "kindle_physical",
    val coverUri: String? = null,
    val progressUnit: ProgressUnit = ProgressUnit.PAGES,
    val currentPosition: Int = 0,
    val totalUnits: Int = 0,
    val isCurrentlyReading: Boolean = false,
    val totalPages: Int? = null,
    val totalDurationSeconds: Long? = null,
    val currentPage: Int? = null,
    val currentDurationSeconds: Long? = null,
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis()
) {
    val progressPercentage: Int
        get() = if (totalUnits > 0) ((currentPosition.toFloat() / totalUnits) * 100).toInt().coerceIn(0, 100) else 0

    val unitLabel: String
        get() = when (progressUnit) {
            ProgressUnit.PAGES -> "Pág."
            ProgressUnit.LOCATIONS -> "Loc"
        }

    val formattedProgress: String
        get() = if (totalUnits > 0) {
            "$unitLabel $currentPosition de $totalUnits ($progressPercentage%)"
        } else if (currentPosition > 0) {
            "$unitLabel $currentPosition"
        } else {
            "Sin empezar"
        }
}
