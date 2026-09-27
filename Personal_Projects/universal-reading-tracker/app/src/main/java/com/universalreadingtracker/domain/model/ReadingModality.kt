package com.universalreadingtracker.domain.model

/**
 * Implements ADR-007 from decisions.md:
 * Modalities of reading supported by the application.
 */
enum class ReadingModality {
    AUDIOBOOK,       // Listening via Audible, Spotify, etc.
    EBOOK_KINDLE,    // Reading on physical Amazon Kindle hardware
    PHYSICAL_BOOK,   // Printed paper book
    OTHER_EBOOK      // Other digital readers
}

enum class BookFormat {
    AUDIOBOOK,
    EBOOK,
    PHYSICAL,
    HYBRID           // Same book consumed in both audio and text (ADR-007)
}

enum class SessionStatus {
    RECORDING,
    PAUSED,
    CONFIRMED,
    DISCARDED
}

enum class ProgressUnit {
    PAGES,      // Pág. 120 de 350
    LOCATIONS   // Loc 2.450 de 6.800 (Kindle)
}
