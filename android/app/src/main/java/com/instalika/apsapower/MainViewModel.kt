package com.instalika.apsapower

import android.app.Application
import android.content.Intent
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.instalika.apsapower.data.Computer
import com.instalika.apsapower.data.ComputerRepository
import com.instalika.apsapower.data.WolSettings
import com.instalika.apsapower.net.NetworkHelper
import com.instalika.apsapower.wol.WolSender
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class UiMessage(
    val text: String,
    val isError: Boolean = false,
)

class MainViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = ComputerRepository(application)
    private val app = application.applicationContext

    val computers: StateFlow<List<Computer>> = repository.computers
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val packetRepeats: StateFlow<Int> = repository.packetRepeats
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), WolSettings.DEFAULT_REPEATS)

    private val _message = MutableStateFlow<UiMessage?>(null)
    val message: StateFlow<UiMessage?> = _message.asStateFlow()

    private val _showEditor = MutableStateFlow<Computer?>(null)
    val showEditor: StateFlow<Computer?> = _showEditor.asStateFlow()

    private val _showSettings = MutableStateFlow(false)
    val showSettings: StateFlow<Boolean> = _showSettings.asStateFlow()

    val isOnWifi: Boolean
        get() = NetworkHelper.isOnWifi(app)

    val suggestedBroadcast: String
        get() = NetworkHelper.getSubnetBroadcast(app) ?: "255.255.255.255"

    fun wake(computer: Computer) {
        viewModelScope.launch {
            try {
                val repeats = repository.getPacketRepeats()
                withContext(Dispatchers.IO) {
                    WolSender.sendMagicPacket(
                        mac = computer.mac,
                        broadcast = computer.broadcast,
                        port = computer.port,
                        repeats = repeats,
                    )
                }
                _message.value = UiMessage("Įjungta: ${computer.name} ($repeats× paketai)")
            } catch (e: Exception) {
                _message.value = UiMessage(e.message ?: "Klaida", isError = true)
            }
        }
    }

    fun wakeAll() {
        viewModelScope.launch {
            val list = computers.value
            if (list.isEmpty()) {
                _message.value = UiMessage("Nėra kompiuterių", isError = true)
                return@launch
            }
            try {
                val repeats = repository.getPacketRepeats()
                withContext(Dispatchers.IO) {
                    for (computer in list) {
                        WolSender.sendMagicPacket(
                            mac = computer.mac,
                            broadcast = computer.broadcast,
                            port = computer.port,
                            repeats = repeats,
                        )
                    }
                }
                _message.value = UiMessage("Įjungimo signalas išsiųstas: ${list.size} komp.")
            } catch (e: Exception) {
                _message.value = UiMessage(e.message ?: "Klaida", isError = true)
            }
        }
    }

    fun wakeByMac(mac: String, broadcast: String, port: Int = 9) {
        viewModelScope.launch {
            try {
                val repeats = repository.getPacketRepeats()
                withContext(Dispatchers.IO) {
                    WolSender.sendMagicPacket(
                        mac = mac,
                        broadcast = broadcast.ifBlank { suggestedBroadcast },
                        port = port,
                        repeats = repeats,
                    )
                }
                _message.value = UiMessage("Įjungta: ${WolSender.normalizeMac(mac)}")
            } catch (e: Exception) {
                _message.value = UiMessage(e.message ?: "Klaida", isError = true)
            }
        }
    }

    fun openEditor(computer: Computer? = null) {
        _showEditor.value = computer ?: Computer(
            id = repository.newId(),
            name = "",
            mac = "",
            broadcast = suggestedBroadcast,
        )
    }

    fun closeEditor() {
        _showEditor.value = null
    }

    fun openSettings() {
        _showSettings.value = true
    }

    fun closeSettings() {
        _showSettings.value = false
    }

    fun setPacketRepeats(repeats: Int) {
        viewModelScope.launch {
            repository.setPacketRepeats(repeats)
            _message.value = UiMessage("Paketų skaičius: $repeats")
        }
    }

    fun saveComputer(computer: Computer) {
        viewModelScope.launch {
            if (computer.name.isBlank()) {
                _message.value = UiMessage("Įveskite kompiuterio vardą", isError = true)
                return@launch
            }
            if (!WolSender.isValidMac(computer.mac)) {
                _message.value = UiMessage("Neteisingas MAC adresas", isError = true)
                return@launch
            }
            repository.save(
                computer.copy(
                    mac = WolSender.normalizeMac(computer.mac),
                    broadcast = computer.broadcast.ifBlank { suggestedBroadcast },
                ),
            )
            _showEditor.value = null
            _message.value = UiMessage("Išsaugota: ${computer.name}")
        }
    }

    fun deleteComputer(id: String) {
        viewModelScope.launch {
            repository.delete(id)
            _message.value = UiMessage("Kompiuteris pašalintas")
        }
    }

    fun importFromUri(uri: Uri) {
        viewModelScope.launch {
            try {
                val raw = withContext(Dispatchers.IO) {
                    app.contentResolver.openInputStream(uri)?.bufferedReader()?.readText()
                } ?: throw IllegalArgumentException("Nepavyko nuskaityti failo")
                val count = repository.importFromJson(raw)
                _message.value = UiMessage("Importuota: $count komp.")
            } catch (e: Exception) {
                _message.value = UiMessage(e.message ?: "Importo klaida", isError = true)
            }
        }
    }

    fun writeExportToUri(uri: Uri) {
        viewModelScope.launch {
            try {
                val json = repository.exportJson()
                withContext(Dispatchers.IO) {
                    app.contentResolver.openOutputStream(uri)?.use { stream ->
                        stream.write(json.toByteArray(Charsets.UTF_8))
                    }
                }
                _message.value = UiMessage("Eksportuota į failą")
            } catch (e: Exception) {
                _message.value = UiMessage(e.message ?: "Eksporto klaida", isError = true)
            }
        }
    }

    suspend fun buildShareIntent(): Intent {
        val json = repository.exportJson()
        return Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_SUBJECT, "Instalika Power kompiuteriai")
            putExtra(Intent.EXTRA_TEXT, json)
        }
    }

    fun clearMessage() {
        _message.value = null
    }
}
