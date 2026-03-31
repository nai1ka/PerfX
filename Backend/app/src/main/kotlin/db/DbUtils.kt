package com.perfx.db

import kotlinx.coroutines.Dispatchers
import org.jetbrains.exposed.v1.core.Transaction
import org.jetbrains.exposed.v1.jdbc.transactions.suspendTransaction

suspend fun <T> suspendTransaction(block: Transaction.() -> T): T =
    with(Dispatchers.IO) {
        suspendTransaction(statement = block)
    }

