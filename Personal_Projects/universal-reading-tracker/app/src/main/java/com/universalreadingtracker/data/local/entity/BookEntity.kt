package com.universalreadingtracker.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.universalreadingtracker.domain.model.Book
import com.universalreadingtracker.domain.model.BookFormat
import com.universalreadingtracker.domain.model.ProgressUnit

/**
 * Room Entity for local-first book storage.
 * Implements Section 3 from spec.md & ADR-006.
 * Supports Pages and Kindle Locations (Loc).
 */
@Entity(tableName = "books")
data class BookEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val title: String,
    val author: String,
    val format: String = BookFormat.EBOOK.name,
    val primaryProviderId: String = "kindle_physical",
    val coverUri: String? = null,
    val progressUnit: String = ProgressUnit.PAGES.name,
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
    fun toDomain(): Book = Book(
        id = id,
        title = title,
        author = author,
        format = try { BookFormat.valueOf(format) } catch (e: Exception) { BookFormat.EBOOK },
        primaryProviderId = primaryProviderId,
        coverUri = coverUri,
        progressUnit = try { ProgressUnit.valueOf(progressUnit) } catch (e: Exception) { ProgressUnit.PAGES },
        currentPosition = currentPosition,
        totalUnits = totalUnits,
        isCurrentlyReading = isCurrentlyReading,
        totalPages = totalPages ?: totalUnits,
        totalDurationSeconds = totalDurationSeconds,
        currentPage = currentPage ?: currentPosition,
        currentDurationSeconds = currentDurationSeconds,
        createdAt = createdAt,
        updatedAt = updatedAt
    )

    companion object {
        fun fromDomain(domain: Book): BookEntity = BookEntity(
            id = domain.id,
            title = domain.title,
            author = domain.author,
            format = domain.format.name,
            primaryProviderId = domain.primaryProviderId,
            coverUri = domain.coverUri,
            progressUnit = domain.progressUnit.name,
            currentPosition = domain.currentPosition,
            totalUnits = domain.totalUnits,
            isCurrentlyReading = domain.isCurrentlyReading,
            totalPages = domain.totalPages ?: domain.totalUnits,
            totalDurationSeconds = domain.totalDurationSeconds,
            currentPage = domain.currentPage ?: domain.currentPosition,
            currentDurationSeconds = domain.currentDurationSeconds,
            createdAt = domain.createdAt,
            updatedAt = domain.updatedAt
        )
    }
}
