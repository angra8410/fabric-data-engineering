package com.universalreadingtracker.data.provider

import com.universalreadingtracker.domain.model.ReadingModality
import com.universalreadingtracker.domain.provider.ReadingProviderAdapter

/**
 * Implements RF-03, RF-04, ADR-007 and ADR-008 from spec.md & decisions.md:
 * Specialized adapter for reading sessions performed on a physical Amazon Kindle device
 * (Paperwhite, Oasis, Scribe, Basic).
 */
class KindlePhysicalProviderAdapter : ReadingProviderAdapter {

    override val providerId: String = "kindle_physical"
    override val displayName: String = "Kindle (Dispositivo Físico)"
    override val supportedModality: ReadingModality = ReadingModality.EBOOK_KINDLE

    override fun canHandle(sourceIdentifier: String): Boolean {
        return sourceIdentifier.equals("kindle", ignoreCase = true) ||
               sourceIdentifier.equals("kindle_physical", ignoreCase = true)
    }
}
