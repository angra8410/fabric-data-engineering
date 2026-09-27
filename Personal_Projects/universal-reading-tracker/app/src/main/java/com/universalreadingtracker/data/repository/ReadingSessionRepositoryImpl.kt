package com.universalreadingtracker.data.repository

import com.universalreadingtracker.data.local.dao.DailyReadingSummaryDao
import com.universalreadingtracker.data.local.dao.ReadingSessionDao
import com.universalreadingtracker.data.local.entity.DailyReadingSummaryEntity
import com.universalreadingtracker.data.local.entity.ReadingSessionEntity
import com.universalreadingtracker.domain.model.DailyReadingSummary
import com.universalreadingtracker.domain.model.ReadingModality
import com.universalreadingtracker.domain.model.ReadingSession
import com.universalreadingtracker.domain.repository.ReadingSessionRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

class ReadingSessionRepositoryImpl(
    private val sessionDao: ReadingSessionDao,
    private val summaryDao: DailyReadingSummaryDao
) : ReadingSessionRepository {

    private val dateFormatter = DateTimeFormatter.ISO_LOCAL_DATE

    override fun getAllSessions(): Flow<List<ReadingSession>> {
        return sessionDao.getAllSessions().map { entities -> entities.map { it.toDomain() } }
    }

    override fun getSessionsForDate(dateString: String): Flow<List<ReadingSession>> {
        // Calculate epoch start and end for date
        val localDate = java.time.LocalDate.parse(dateString, dateFormatter)
        val startOfDayEpoch = localDate.atStartOfDay(ZoneId.systemDefault()).toInstant().toEpochMilli()
        val endOfDayEpoch = localDate.plusDays(1).atStartOfDay(ZoneId.systemDefault()).toInstant().toEpochMilli() - 1
        return sessionDao.getSessionsForEpochRange(startOfDayEpoch, endOfDayEpoch)
            .map { entities -> entities.map { it.toDomain() } }
    }

    override suspend fun insertSession(session: ReadingSession): Long {
        val entity = ReadingSessionEntity.fromDomain(session)
        val id = sessionDao.insertSession(entity)

        // Automatically update the aggregated daily summary for this session's date
        val sessionDate = Instant.ofEpochMilli(session.startTime)
            .atZone(ZoneId.systemDefault())
            .toLocalDate()
            .format(dateFormatter)

        val existingSummary = summaryDao.getSummaryForDate(sessionDate)
        val addedMinutes = session.durationMinutes
        val isAudio = session.modality == ReadingModality.AUDIOBOOK
        val isKindle = session.modality == ReadingModality.EBOOK_KINDLE
        val isPhysical = session.modality == ReadingModality.PHYSICAL_BOOK

        val updatedSummary = if (existingSummary != null) {
            val newTotal = existingSummary.totalMinutesRead + addedMinutes
            existingSummary.copy(
                totalMinutesRead = newTotal,
                audioMinutes = existingSummary.audioMinutes + if (isAudio) addedMinutes else 0,
                kindleMinutes = existingSummary.kindleMinutes + if (isKindle) addedMinutes else 0,
                physicalMinutes = existingSummary.physicalMinutes + if (isPhysical) addedMinutes else 0,
                goalReached = newTotal >= 30
            )
        } else {
            DailyReadingSummaryEntity(
                date = sessionDate,
                totalMinutesRead = addedMinutes,
                audioMinutes = if (isAudio) addedMinutes else 0,
                kindleMinutes = if (isKindle) addedMinutes else 0,
                physicalMinutes = if (isPhysical) addedMinutes else 0,
                goalReached = addedMinutes >= 30,
                isHistoricalBackfill = false
            )
        }

        summaryDao.insertOrUpdateSummary(updatedSummary)
        return id
    }

    override suspend fun getDailySummaries(limitDays: Int): Flow<List<DailyReadingSummary>> {
        return summaryDao.getDailySummaries(limitDays).map { list -> list.map { it.toDomain() } }
    }

    override suspend fun getSummaryForDate(dateString: String): DailyReadingSummary? {
        return summaryDao.getSummaryForDate(dateString)?.toDomain()
    }

    override fun observeSummaryForDate(dateString: String): Flow<DailyReadingSummary?> {
        return summaryDao.observeSummaryForDate(dateString).map { it?.toDomain() }
    }

    override suspend fun saveDailySummary(summary: DailyReadingSummary) {
        summaryDao.insertOrUpdateSummary(DailyReadingSummaryEntity.fromDomain(summary))
    }
}
