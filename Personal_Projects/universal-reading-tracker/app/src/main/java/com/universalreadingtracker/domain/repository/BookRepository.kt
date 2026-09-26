package com.universalreadingtracker.domain.repository

import com.universalreadingtracker.domain.model.Book
import kotlinx.coroutines.flow.Flow

interface BookRepository {
    fun getAllBooks(): Flow<List<Book>>
    suspend fun getBookById(id: Long): Book?
    suspend fun findOrCreateBook(title: String, author: String, providerId: String): Book
    suspend fun insertOrUpdateBook(book: Book): Long
    suspend fun updateBookProgress(bookId: Long, newPage: Int?, addedDurationSeconds: Long?)
}
