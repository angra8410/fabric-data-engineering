package com.universalreadingtracker.domain.model

/**
 * Domain entity representing a Book in the local catalog.
 * Implements Section 3 (Domain Model) from spec.md.
 */
data class Book(
    val id: Long = 0,
    val title: String,
    val author: String,
    val format: BookFormat = BookFormat.AUDIOBOOK,
    val primaryProviderId: String = "audible",
    val coverUri: String? = null,
    val totalPages: Int? = null,
    val totalDurationSeconds: Long? = null,
    val currentPage: Int? = null,
    val currentDurationSeconds: Long? = null,
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis()
)
