package com.ndevelop.sdk.data

import android.content.Context
import androidx.room.Dao
import androidx.room.Database
import androidx.room.Insert
import androidx.room.Query
import androidx.room.Room
import androidx.room.RoomDatabase

@Dao
interface MetricDao {
    @Insert
    suspend fun insertAll(metrics: List<MetricDb>)

    @Query("SELECT * FROM metrics LIMIT :limit")
    suspend fun getBatch(limit: Int): List<MetricDb>

    @Query("DELETE FROM metrics WHERE id IN (:ids)")
    suspend fun deleteMetrics(ids: List<Long>)

    @Query("SELECT COUNT(*) FROM metrics")
    suspend fun getCount(): Int
}

@Database(entities = [MetricDb::class], version = 1)
abstract class MetricDatabase : RoomDatabase() {
    abstract fun metricDao(): MetricDao

    companion object {
        @Volatile
        private var instance: MetricDatabase? = null
        fun getInstance(context: Context): MetricDatabase =
            instance ?: synchronized(this) {
                Room.databaseBuilder(context, MetricDatabase::class.java, "metrics.db").build()
                    .also { instance = it }
            }
    }
}