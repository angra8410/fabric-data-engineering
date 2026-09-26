package com.universalreadingtracker.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.universalreadingtracker.domain.model.Book
import com.universalreadingtracker.domain.model.BookFormat

/**
 * Room Entity for local-first book storage.
 * Implements Section 3 from spec.md & ADR-006.
 */
@Entity(tableName = "books")
data class BookEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val title: String,
    val author: String,
    val format: String = BookFormat.AUDIOBOOK.name,
    val primaryProviderId: String = "audible",
    val coverUri: String? = null,
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
        format = try { BookFormat.valueOf(format) } catch (e: Exception) { BookFormat.AUDIOBOOK },
        primaryProviderId = primaryProviderId,
        coverUri = coverUri,
        totalPages = totalPages,
        totalDurationSeconds = totalDurationSeconds,
        currentPage = currentPage,
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
            totalPages = domain.totalPages,
            totalDurationSeconds = domain.totalDurationSeconds,
            currentPage = domain.currentPage,
            currentDurationSeconds = domain.currentDurationSeconds,
            createdAt = domain.createdAt,
            updatedAt = domain.updatedAt
        )
    }
}
