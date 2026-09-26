package com.universalreadingtracker.domain.model

/**
 * Domain entity representing an individual reading session.
 * Implements Section 3 (Domain Model), RF-03 (Wall-clock real time) and ADR-002 from spec.md & decisions.md.
 */
data class ReadingSession(
    val id: Long = 0,
    val bookId: Long,
    val bookTitle: String = "",
    val bookAuthor: String = "",
    val modality: ReadingModality,
    val providerId: String,
    val startTime: Long,
    val endTime: Long,
    val realDurationSeconds: Long, // Net wall-clock time excluding pauses (ADR-002)
    val startPage: Int? = null,
    val endPage: Int? = null,
    val pagesRead: Int? = if (startPage != null && endPage != null) maxOf(0, endPage - startPage) else null,
    val status: SessionStatus = SessionStatus.CONFIRMED,
    val notes: String? = null,
    val detectedPlaybackSpeed: Float? = null
) {
    val durationMinutes: Int
        get() = (realDurationSeconds / 60).toInt()
}
