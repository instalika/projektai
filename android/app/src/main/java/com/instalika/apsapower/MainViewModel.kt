package com.instalika.apsapower

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.instalika.apsapower.data.Computer
import com.instalika.apsapower.data.ComputerRepository
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

    val computers: StateFlow<List<Computer>> = repository.computers
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    private val _message = MutableStateFlow<UiMessage?>(null)
    val message: StateFlow<UiMessage?> = _message.asStateFlow()

    private val _showEditor = MutableStateFlow<Computer?>(null)
    val showEditor: StateFlow<Computer?> = _showEditor.asStateFlow()

    init {
        viewModelScope.launch {
            repository.importDefaults(
                listOf(
                    Computer(
                        id = "demo-1",
                        name = "Biuro PC",
                        mac = "AA:BB:CC:DD:EE:FF",
                        broadcast = "192.168.1.255",
                        description = "Pakeiskite MAC adresą",
                    ),
                ),
            )
        }
    }

    fun wake(computer: Computer) {
        viewModelScope.launch {
            try {
                withContext(Dispatchers.IO) {
                    WolSender.sendMagicPacket(computer.mac, computer.broadcast)
                }
                _message.value = UiMessage("Įjungimo signalas išsiųstas: ${computer.name}")
            } catch (e: Exception) {
                _message.value = UiMessage(e.message ?: "Klaida", isError = true)
            }
        }
    }

    fun wakeByMac(mac: String, broadcast: String) {
        viewModelScope.launch {
            try {
                withContext(Dispatchers.IO) {
                    WolSender.sendMagicPacket(mac, broadcast.ifBlank { "255.255.255.255" })
                }
                _message.value = UiMessage("Įjungimo signalas išsiųstas: ${WolSender.normalizeMac(mac)}")
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
            broadcast = "255.255.255.255",
        )
    }

    fun closeEditor() {
        _showEditor.value = null
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
            repository.save(computer.copy(mac = WolSender.normalizeMac(computer.mac)))
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

    fun clearMessage() {
        _message.value = null
    }
}
