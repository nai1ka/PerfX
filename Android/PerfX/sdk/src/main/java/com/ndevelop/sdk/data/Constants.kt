package com.ndevelop.sdk.data

object Constants {

    // В памяти может быть не более 100 метрик
    const val MEMORY_LIMIT = 20

    // Порог на диске для запуска синхронизации с сервером
    const val DISK_SYNC_THRESHOLD = 20

    // Абсолютный максимум записей на диске — при превышении удаляются старые
    const val DISK_HARD_LIMIT = 1000
}

