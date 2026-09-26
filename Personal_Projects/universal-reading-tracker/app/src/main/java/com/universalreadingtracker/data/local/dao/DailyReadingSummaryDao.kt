package com.universalreadingtracker.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.universalreadingtracker.data.local.entity.DailyReadingSummaryEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface DailyReadingSummaryDao {
    @Query("SELECT * FROM daily_reading_summaries ORDER BY date DESC LIMIT :limitDays")
    fun getDailySummaries(limitDays: Int = 365): Flow<List<DailyReadingSummaryEntity>>

    @Query("SELECT * FROM daily_reading_summaries WHERE date = :dateString LIMIT 1")
    suspend fun getSummaryForDate(dateString: String): DailyReadingSummaryEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrUpdateSummary(summary: DailyReadingSummaryEntity)

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertAll(summaries: List<DailyReadingSummaryEntity>)

    @Query("SELECT COUNT(*) FROM daily_reading_summaries WHERE isHistoricalBackfill = 1")
    suspend fun countHistoricalBackfillDays(): Int

    @Query("SELECT COUNT(*) FROM daily_reading_summaries WHERE totalMinutesRead >= 1 OR isHistoricalBackfill = 1")
    suspend fun countTotalValidStreakDays(): Int
}
