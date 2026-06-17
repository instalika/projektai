package com.instalika.apsapower.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.util.UUID

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "instalika_power")

class ComputerRepository(private val context: Context) {
    private val json = Json { ignoreUnknownKeys = true }

    val computers: Flow<List<Computer>> = context.dataStore.data.map { prefs ->
        decode(prefs[COMPUTERS_KEY])
    }

    val packetRepeats: Flow<Int> = context.dataStore.data.map { prefs ->
        prefs[REPEATS_KEY] ?: WolSettings.DEFAULT_REPEATS
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

    suspend fun replaceAll(computers: List<Computer>) {
        context.dataStore.edit { prefs ->
            prefs[COMPUTERS_KEY] = json.encodeToString(computers)
        }
    }

    suspend fun mergeImport(incoming: List<Computer>) {
        context.dataStore.edit { prefs ->
            val current = decode(prefs[COMPUTERS_KEY]).associateBy { it.mac.uppercase() }.toMutableMap()
            for (computer in incoming) {
                val key = computer.mac.uppercase()
                val existing = current[key]
                current[key] = if (existing != null) {
                    computer.copy(id = existing.id)
                } else {
                    computer.copy(id = computer.id.ifBlank { newId() })
                }
            }
            prefs[COMPUTERS_KEY] = json.encodeToString(current.values.toList())
        }
    }

    suspend fun exportJson(): String {
        val list = decode(context.dataStore.data.first()[COMPUTERS_KEY])
        return json.encodeToString(list)
    }

    suspend fun importFromJson(raw: String): Int {
        val imported = parseImport(raw)
        if (imported.isEmpty()) throw IllegalArgumentException("Tuščias arba neteisingas failas")
        mergeImport(imported)
        return imported.size
    }

    suspend fun setPacketRepeats(repeats: Int) {
        context.dataStore.edit { prefs ->
            prefs[REPEATS_KEY] = repeats.coerceIn(1, 10)
        }
    }

    suspend fun getPacketRepeats(): Int =
        context.dataStore.data.first()[REPEATS_KEY] ?: WolSettings.DEFAULT_REPEATS

    fun newId(): String = UUID.randomUUID().toString()

    private fun decode(raw: String?): List<Computer> =
        runCatching { json.decodeFromString<List<Computer>>(raw ?: "[]") }.getOrDefault(emptyList())

    private fun parseImport(raw: String): List<Computer> {
        val element = json.parseToJsonElement(raw.trim())
        return when (element) {
            is JsonArray -> element.mapNotNull { parseComputerElement(it, null) }
            is JsonObject -> element.map { (name, value) ->
                parseComputerElement(value, name)
            }.filterNotNull()
            else -> emptyList()
        }
    }

    private fun parseComputerElement(element: JsonElement, name: String?): Computer? {
        val obj = element.jsonObject
        val mac = obj["mac"]?.jsonPrimitive?.content ?: return null
        return Computer(
            id = newId(),
            name = name ?: obj["name"]?.jsonPrimitive?.content ?: "Kompiuteris",
            mac = mac,
            broadcast = obj["broadcast"]?.jsonPrimitive?.content ?: "255.255.255.255",
            port = obj["port"]?.jsonPrimitive?.content?.toIntOrNull() ?: 9,
            description = obj["description"]?.jsonPrimitive?.content ?: "",
        )
    }

    companion object {
        private val COMPUTERS_KEY = stringPreferencesKey("computers")
        private val REPEATS_KEY = intPreferencesKey("packet_repeats")
    }
}

object WolSettings {
    const val DEFAULT_REPEATS = 3
}

@Serializable
data class ComputerExport(
    val computers: List<Computer>,
)
