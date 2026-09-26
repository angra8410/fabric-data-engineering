package com.universalreadingtracker.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.universalreadingtracker.domain.model.DailyReadingSummary

/**
 * Room Entity for aggregated daily reading summaries and historical streak tracking.
 * Implements Section 3, RF-08, RF-09 and ADR-009 from spec.md & decisions.md.
 */
@Entity(tableName = "daily_reading_summaries")
data class DailyReadingSummaryEntity(
    @PrimaryKey
    val date: String, // ISO date string: YYYY-MM-DD
    val totalMinutesRead: Int,
    val audioMinutes: Int,
    val kindleMinutes: Int,
    val physicalMinutes: Int,
    val goalReached: Boolean,
    val isHistoricalBackfill: Boolean = false
) {
    fun toDomain(): DailyReadingSummary = DailyReadingSummary(
        date = date,
        totalMinutesRead = totalMinutesRead,
        audioMinutes = audioMinutes,
        kindleMinutes = kindleMinutes,
        physicalMinutes = physicalMinutes,
        goalReached = goalReached,
        isHistoricalBackfill = isHistoricalBackfill
    )

    companion object {
        fun fromDomain(domain: DailyReadingSummary): DailyReadingSummaryEntity = DailyReadingSummaryEntity(
            date = domain.date,
            totalMinutesRead = domain.totalMinutesRead,
            audioMinutes = domain.audioMinutes,
            kindleMinutes = domain.kindleMinutes,
            physicalMinutes = domain.physicalMinutes,
            goalReached = domain.goalReached,
            isHistoricalBackfill = domain.isHistoricalBackfill
        )
    }
}
