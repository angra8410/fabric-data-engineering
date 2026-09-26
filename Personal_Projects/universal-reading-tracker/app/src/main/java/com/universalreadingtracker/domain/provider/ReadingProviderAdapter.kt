package com.universalreadingtracker.domain.provider

import com.universalreadingtracker.domain.model.ReadingModality

/**
 * Metadata extracted from active audio playback.
 */
data class AudioPlaybackMetadata(
    val title: String,
    val author: String,
    val albumOrSeries: String? = null,
    val durationSeconds: Long? = null,
    val positionSeconds: Long? = null,
    val isPlaying: Boolean = false,
    val playbackSpeed: Float = 1.0f
)

/**
 * Implements ADR-003 and RF-07 from spec.md & decisions.md:
 * Decoupled provider adapter abstraction.
 * Allows pluggable integrations (Audible, Spotify, Storytel, Kindle Physical, etc.)
 */
interface ReadingProviderAdapter {
    val providerId: String
    val displayName: String
    val supportedModality: ReadingModality

    /**
     * Checks if this provider can handle the given package name or external trigger.
     */
    fun canHandle(sourceIdentifier: String): Boolean
}

/**
 * Specialized adapter for audio streaming services via MediaSession.
 */
interface AudioPlaybackProviderAdapter : ReadingProviderAdapter {
    val targetPackageName: String

    override fun canHandle(sourceIdentifier: String): Boolean {
        return sourceIdentifier.equals(targetPackageName, ignoreCase = true)
    }

    /**
     * Filters whether the media session belongs to an audiobook (and not music/podcast in mixed apps).
     */
    fun isAudiobookContent(metadata: AudioPlaybackMetadata): Boolean
}
