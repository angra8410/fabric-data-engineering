package com.universalreadingtracker.data.local.entity

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import com.universalreadingtracker.domain.model.ReadingModality
import com.universalreadingtracker.domain.model.ReadingSession
import com.universalreadingtracker.domain.model.SessionStatus

/**
 * Room Entity for individual reading sessions.
 * Implements Section 3, RF-03 and ADR-002 from spec.md & decisions.md.
 */
@Entity(
    tableName = "reading_sessions",
    foreignKeys = [
        ForeignKey(
            entity = BookEntity::class,
            parentColumns = ["id"],
            childColumns = ["bookId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [
        Index(value = ["bookId"]),
        Index(value = ["startTime"])
    ]
)
data class ReadingSessionEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val bookId: Long,
    val bookTitle: String = "",
    val bookAuthor: String = "",
    val modality: String,
    val providerId: String,
    val startTime: Long,
    val endTime: Long,
    val realDurationSeconds: Long,
    val startPage: Int? = null,
    val endPage: Int? = null,
    val status: String = SessionStatus.CONFIRMED.name,
    val notes: String? = null,
    val detectedPlaybackSpeed: Float? = null
) {
    fun toDomain(): ReadingSession = ReadingSession(
        id = id,
        bookId = bookId,
        bookTitle = bookTitle,
        bookAuthor = bookAuthor,
        modality = try { ReadingModality.valueOf(modality) } catch (e: Exception) { ReadingModality.AUDIOBOOK },
        providerId = providerId,
        startTime = startTime,
        endTime = endTime,
        realDurationSeconds = realDurationSeconds,
        startPage = startPage,
        endPage = endPage,
        status = try { SessionStatus.valueOf(status) } catch (e: Exception) { SessionStatus.CONFIRMED },
        notes = notes,
        detectedPlaybackSpeed = detectedPlaybackSpeed
    )

    companion object {
        fun fromDomain(domain: ReadingSession): ReadingSessionEntity = ReadingSessionEntity(
            id = domain.id,
            bookId = domain.bookId,
            bookTitle = domain.bookTitle,
            bookAuthor = domain.bookAuthor,
            modality = domain.modality.name,
            providerId = domain.providerId,
            startTime = domain.startTime,
            endTime = domain.endTime,
            realDurationSeconds = domain.realDurationSeconds,
            startPage = domain.startPage,
            endPage = domain.endPage,
            status = domain.status.name,
            notes = domain.notes,
            detectedPlaybackSpeed = domain.detectedPlaybackSpeed
        )
    }
}
