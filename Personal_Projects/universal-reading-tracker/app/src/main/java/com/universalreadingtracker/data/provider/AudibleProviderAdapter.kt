package com.universalreadingtracker.data.provider

import com.universalreadingtracker.domain.model.ReadingModality
import com.universalreadingtracker.domain.provider.AudioPlaybackMetadata
import com.universalreadingtracker.domain.provider.AudioPlaybackProviderAdapter

/**
 * Implements RF-01, RF-05, ADR-001 and ADR-003 from spec.md & decisions.md:
 * Specialized adapter for Audible (Amazon).
 * Intercepts media events from 'com.audible.application'.
 */
class AudibleProviderAdapter : AudioPlaybackProviderAdapter {

    override val providerId: String = "audible"
    override val displayName: String = "Audible"
    override val supportedModality: ReadingModality = ReadingModality.AUDIOBOOK
    override val targetPackageName: String = "com.audible.application"

    /**
     * Audible is a dedicated audiobook platform; any active playback from its package
     * is guaranteed to be audiobook or lecture content.
     */
    override fun isAudiobookContent(metadata: AudioPlaybackMetadata): Boolean {
        return metadata.title.isNotBlank()
    }
}
