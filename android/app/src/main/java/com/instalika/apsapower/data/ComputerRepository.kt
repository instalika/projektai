package com.instalika.apsapower.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.util.UUID

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "apsa_power")

class ComputerRepository(private val context: Context) {
    private val json = Json { ignoreUnknownKeys = true }

    val computers: Flow<List<Computer>> = context.dataStore.data.map { prefs ->
        val raw = prefs[COMPUTERS_KEY] ?: "[]"
        runCatching { json.decodeFromString<List<Computer>>(raw) }.getOrDefault(emptyList())
    }

    suspend fun save(computer: Computer) {
        context.dataStore.edit { prefs ->
            val current = decode(prefs[COMPUTERS_KEY])
            val updated = current.filter { it.id != computer.id } + computer
            prefs[COMPUTERS_KEY] = json.encodeToString(updated)
        }
    }

    suspend fun delete(id: String) {
        context.dataStore.edit { prefs ->
            val updated = decode(prefs[COMPUTERS_KEY]).filter { it.id != id }
            prefs[COMPUTERS_KEY] = json.encodeToString(updated)
        }
    }

    suspend fun importDefaults(defaults: List<Computer>) {
        context.dataStore.edit { prefs ->
            if (decode(prefs[COMPUTERS_KEY]).isNotEmpty()) return@edit
            prefs[COMPUTERS_KEY] = json.encodeToString(defaults)
        }
    }

    fun newId(): String = UUID.randomUUID().toString()

    private fun decode(raw: String?): List<Computer> =
        runCatching { json.decodeFromString<List<Computer>>(raw ?: "[]") }.getOrDefault(emptyList())

    companion object {
        private val COMPUTERS_KEY = stringPreferencesKey("computers")
    }
}
