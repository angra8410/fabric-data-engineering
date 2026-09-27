package com.universalreadingtracker.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import androidx.room.Update
import com.universalreadingtracker.data.local.entity.BookEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface BookDao {
    @Query("SELECT * FROM books ORDER BY isCurrentlyReading DESC, updatedAt DESC")
    fun getAllBooks(): Flow<List<BookEntity>>

    @Query("SELECT * FROM books WHERE isCurrentlyReading = 1 LIMIT 1")
    fun getActiveReadingBook(): Flow<BookEntity?>

    @Query("SELECT * FROM books WHERE isCurrentlyReading = 1 LIMIT 1")
    suspend fun getActiveReadingBookSync(): BookEntity?

    @Query("SELECT * FROM books WHERE id = :id LIMIT 1")
    suspend fun getBookById(id: Long): BookEntity?

    @Query("SELECT * FROM books WHERE LOWER(title) = LOWER(:title) AND LOWER(author) = LOWER(:author) LIMIT 1")
    suspend fun findByTitleAndAuthor(title: String, author: String): BookEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBook(book: BookEntity): Long

    @Update
    suspend fun updateBook(book: BookEntity)

    @Query("UPDATE books SET currentPosition = :position, currentPage = :position, updatedAt = :timestamp WHERE id = :id")
    suspend fun updatePosition(id: Long, position: Int, timestamp: Long = System.currentTimeMillis())

    @Query("UPDATE books SET isCurrentlyReading = 0")
    suspend fun clearActiveBooks()

    @Query("UPDATE books SET isCurrentlyReading = 1, updatedAt = :timestamp WHERE id = :bookId")
    suspend fun markActiveBook(bookId: Long, timestamp: Long = System.currentTimeMillis())

    @Transaction
    suspend fun setActiveBook(bookId: Long) {
        clearActiveBooks()
        markActiveBook(bookId)
    }
}
