package com.universalreadingtracker.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.universalreadingtracker.data.local.entity.ReadingSessionEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ReadingSessionDao {
    @Query("SELECT * FROM reading_sessions ORDER BY startTime DESC")
    fun getAllSessions(): Flow<List<ReadingSessionEntity>>

    @Query("SELECT * FROM reading_sessions WHERE startTime >= :startOfDayEpoch AND endTime <= :endOfDayEpoch ORDER BY startTime ASC")
    fun getSessionsForEpochRange(startOfDayEpoch: Long, endOfDayEpoch: Long): Flow<List<ReadingSessionEntity>>

    @Query("SELECT * FROM reading_sessions WHERE bookId = :bookId ORDER BY startTime DESC")
    fun getSessionsForBook(bookId: Long): Flow<List<ReadingSessionEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSession(session: ReadingSessionEntity): Long

    @Query("SELECT * FROM reading_sessions ORDER BY startTime DESC")
    suspend fun getAllSessionsSync(): List<ReadingSessionEntity>

    @Query("SELECT * FROM reading_sessions WHERE startTime >= :startOfDayEpoch AND endTime <= :endOfDayEpoch ORDER BY startTime ASC")
    suspend fun getSessionsForEpochRangeSync(startOfDayEpoch: Long, endOfDayEpoch: Long): List<ReadingSessionEntity>

    @Query("DELETE FROM reading_sessions WHERE id = :id")
    suspend fun deleteSession(id: Long)
}
