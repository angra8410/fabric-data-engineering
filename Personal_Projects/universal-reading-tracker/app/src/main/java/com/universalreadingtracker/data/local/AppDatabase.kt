package com.universalreadingtracker.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.universalreadingtracker.data.local.dao.BookDao
import com.universalreadingtracker.data.local.dao.DailyReadingSummaryDao
import com.universalreadingtracker.data.local.dao.ReadingSessionDao
import com.universalreadingtracker.data.local.entity.BookEntity
import com.universalreadingtracker.data.local.entity.DailyReadingSummaryEntity
import com.universalreadingtracker.data.local.entity.ReadingSessionEntity

/**
 * Implements ADR-006: Local-first offline Room Database.
 */
@Database(
    entities = [
        BookEntity::class,
        ReadingSessionEntity::class,
        DailyReadingSummaryEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {

    abstract fun bookDao(): BookDao
    abstract fun readingSessionDao(): ReadingSessionDao
    abstract fun dailyReadingSummaryDao(): DailyReadingSummaryDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "universal_reading_tracker.db"
                ).fallbackToDestructiveMigration()
                 .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
