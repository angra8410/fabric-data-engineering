package com.universalreadingtracker.data.repository

import com.universalreadingtracker.data.local.dao.BookDao
import com.universalreadingtracker.data.local.entity.BookEntity
import com.universalreadingtracker.domain.model.Book
import com.universalreadingtracker.domain.repository.BookRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class BookRepositoryImpl(
    private val bookDao: BookDao
) : BookRepository {

    override fun getAllBooks(): Flow<List<Book>> {
        return bookDao.getAllBooks().map { entities -> entities.map { it.toDomain() } }
    }

    override fun getActiveReadingBook(): Flow<Book?> {
        return bookDao.getActiveReadingBook().map { it?.toDomain() }
    }

    override suspend fun getActiveReadingBookSync(): Book? {
        return bookDao.getActiveReadingBookSync()?.toDomain()
    }

    override suspend fun getBookById(id: Long): Book? {
        return bookDao.getBookById(id)?.toDomain()
    }

    override suspend fun findOrCreateBook(title: String, author: String, providerId: String): Book {
        val existing = bookDao.findByTitleAndAuthor(title, author)
        if (existing != null) {
            return existing.toDomain()
        }
        val newBook = Book(
            title = title,
            author = author,
            primaryProviderId = providerId
        )
        val insertedId = bookDao.insertBook(BookEntity.fromDomain(newBook))
        return newBook.copy(id = insertedId)
    }

    override suspend fun insertOrUpdateBook(book: Book): Long {
        return bookDao.insertBook(BookEntity.fromDomain(book))
    }

    override suspend fun updateBookProgress(bookId: Long, newPage: Int?, addedDurationSeconds: Long?) {
        val existing = bookDao.getBookById(bookId) ?: return
        val pos = newPage ?: existing.currentPosition
        bookDao.updatePosition(bookId, pos)
    }

    override suspend fun updateBookPosition(bookId: Long, newPosition: Int) {
        bookDao.updatePosition(bookId, newPosition)
    }

    override suspend fun setActiveReadingBook(bookId: Long) {
        bookDao.setActiveBook(bookId)
    }
}
