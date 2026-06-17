package com.instalika.apsapower.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.FileDownload
import androidx.compose.material.icons.filled.FileUpload
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Power
import androidx.compose.material.icons.filled.PowerSettingsNew
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.Wifi
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.instalika.apsapower.MainViewModel
import com.instalika.apsapower.data.Computer
import kotlin.math.roundToInt

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    viewModel: MainViewModel,
    onImport: () -> Unit,
    onExport: () -> Unit,
    onShare: () -> Unit,
) {
    val computers by viewModel.computers.collectAsState()
    val message by viewModel.message.collectAsState()
    val editor by viewModel.showEditor.collectAsState()
    val showSettings by viewModel.showSettings.collectAsState()
    val packetRepeats by viewModel.packetRepeats.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    var showQuickWake by remember { mutableStateOf(false) }
    var showMenu by remember { mutableStateOf(false) }
    var quickMac by remember { mutableStateOf("") }
    var quickBroadcast by remember { mutableStateOf(viewModel.suggestedBroadcast) }
    var quickPort by remember { mutableStateOf("9") }

    LaunchedEffect(message) {
        message?.let {
            snackbarHostState.showSnackbar(it.text)
            viewModel.clearMessage()
        }
    }

    Scaffold(
        containerColor = ApsaColors.Background,
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            "Instalika Power",
                            fontWeight = FontWeight.Bold,
                            color = ApsaColors.Accent,
                            fontSize = 20.sp,
                        )
                        Text(
                            "Kompiuterių įjungimas per LAN",
                            color = ApsaColors.Muted,
                            fontSize = 12.sp,
                        )
                    }
                },
                actions = {
                    IconButton(onClick = { showMenu = true }) {
                        Icon(Icons.Default.MoreVert, contentDescription = "Meniu", tint = ApsaColors.Text)
                    }
                    DropdownMenu(expanded = showMenu, onDismissRequest = { showMenu = false }) {
                        DropdownMenuItem(
                            text = { Text("Įjungti visus") },
                            onClick = {
                                showMenu = false
                                viewModel.wakeAll()
                            },
                            leadingIcon = { Icon(Icons.Default.Power, null) },
                        )
                        DropdownMenuItem(
                            text = { Text("Importuoti JSON") },
                            onClick = { showMenu = false; onImport() },
                            leadingIcon = { Icon(Icons.Default.FileUpload, null) },
                        )
                        DropdownMenuItem(
                            text = { Text("Eksportuoti failą") },
                            onClick = { showMenu = false; onExport() },
                            leadingIcon = { Icon(Icons.Default.FileDownload, null) },
                        )
                        DropdownMenuItem(
                            text = { Text("Dalintis sąrašu") },
                            onClick = { showMenu = false; onShare() },
                            leadingIcon = { Icon(Icons.Default.Share, null) },
                        )
                        DropdownMenuItem(
                            text = { Text("Nustatymai") },
                            onClick = { showMenu = false; viewModel.openSettings() },
                            leadingIcon = { Icon(Icons.Default.Settings, null) },
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = ApsaColors.Background),
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { viewModel.openEditor() },
                containerColor = ApsaColors.Accent,
            ) {
                Icon(Icons.Default.Add, contentDescription = "Pridėti", tint = ApsaColors.Text)
            }
        },
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item {
                NetworkStatusCard(
                    isOnWifi = viewModel.isOnWifi,
                    broadcast = viewModel.suggestedBroadcast,
                )
            }

            if (computers.isNotEmpty()) {
                item {
                    OutlinedButton(
                        onClick = { viewModel.wakeAll() },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(10.dp),
                    ) {
                        Icon(Icons.Default.Power, null, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(8.dp))
                        Text("Įjungti visus (${computers.size})")
                    }
                }
            }

            if (computers.isEmpty()) {
                item { EmptyCard() }
            } else {
                items(computers, key = { it.id }) { computer ->
                    ComputerCard(
                        computer = computer,
                        onWake = { viewModel.wake(computer) },
                        onEdit = { viewModel.openEditor(computer) },
                        onDelete = { viewModel.deleteComputer(computer.id) },
                    )
                }
            }

            item {
                QuickWakeCard(onExpand = {
                    quickBroadcast = viewModel.suggestedBroadcast
                    showQuickWake = true
                })
                Spacer(modifier = Modifier.height(80.dp))
            }
        }
    }

    editor?.let { computer ->
        ComputerEditorDialog(
            computer = computer,
            suggestedBroadcast = viewModel.suggestedBroadcast,
            onDismiss = { viewModel.closeEditor() },
            onSave = { viewModel.saveComputer(it) },
        )
    }

    if (showQuickWake) {
        AlertDialog(
            onDismissRequest = { showQuickWake = false },
            containerColor = ApsaColors.Card,
            title = { Text("Greitas įjungimas", color = ApsaColors.Text) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    ApsaTextField(quickMac, { quickMac = it }, "MAC (AA:BB:CC:DD:EE:FF)")
                    ApsaTextField(quickBroadcast, { quickBroadcast = it }, "Broadcast IP")
                    ApsaTextField(quickPort, { quickPort = it }, "UDP prievadas")
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.wakeByMac(quickMac, quickBroadcast, quickPort.toIntOrNull() ?: 9)
                    showQuickWake = false
                }) { Text("Įjungti", color = ApsaColors.Accent) }
            },
            dismissButton = {
                TextButton(onClick = { showQuickWake = false }) {
                    Text("Atšaukti", color = ApsaColors.Muted)
                }
            },
        )
    }

    if (showSettings) {
        SettingsDialog(
            repeats = packetRepeats,
            onDismiss = { viewModel.closeSettings() },
            onSave = { viewModel.setPacketRepeats(it) },
        )
    }
}

@Composable
private fun NetworkStatusCard(isOnWifi: Boolean, broadcast: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (isOnWifi) ApsaColors.Card else ApsaColors.Card,
        ),
        shape = RoundedCornerShape(12.dp),
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                if (isOnWifi) Icons.Default.Wifi else Icons.Default.WifiOff,
                contentDescription = null,
                tint = if (isOnWifi) ApsaColors.Success else ApsaColors.Error,
            )
            Spacer(Modifier.width(10.dp))
            Column {
                Text(
                    if (isOnWifi) "Wi-Fi prijungtas" else "Nėra Wi-Fi – WoL gali neveikti",
                    color = ApsaColors.Text,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Medium,
                )
                if (isOnWifi) {
                    Text("Broadcast: $broadcast", color = ApsaColors.Muted, fontSize = 12.sp)
                }
            }
        }
    }
}

@Composable
private fun EmptyCard() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = ApsaColors.Card),
        shape = RoundedCornerShape(12.dp),
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text("Nėra kompiuterių", fontWeight = FontWeight.SemiBold, color = ApsaColors.Text)
            Spacer(Modifier.height(6.dp))
            Text(
                "Paspauskite + ir pridėkite kompiuterį su MAC adresu.",
                color = ApsaColors.Muted,
                fontSize = 14.sp,
            )
        }
    }
}

@Composable
private fun ComputerCard(
    computer: Computer,
    onWake: () -> Unit,
    onEdit: () -> Unit,
    onDelete: () -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = ApsaColors.Card),
        shape = RoundedCornerShape(12.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(computer.name, fontWeight = FontWeight.SemiBold, color = ApsaColors.Text)
                Text(computer.mac, color = ApsaColors.Muted, fontFamily = FontFamily.Monospace, fontSize = 13.sp)
                Text(
                    "${computer.broadcast}:${computer.port}",
                    color = ApsaColors.Muted,
                    fontSize = 11.sp,
                )
                if (computer.description.isNotBlank()) {
                    Text(computer.description, color = ApsaColors.Muted, fontSize = 12.sp)
                }
            }
            IconButton(onClick = onEdit) {
                Icon(Icons.Default.Edit, contentDescription = "Redaguoti", tint = ApsaColors.Muted)
            }
            IconButton(onClick = onDelete) {
                Icon(Icons.Default.Delete, contentDescription = "Šalinti", tint = ApsaColors.Error)
            }
            Button(
                onClick = onWake,
                colors = ButtonDefaults.buttonColors(containerColor = ApsaColors.Accent),
                shape = RoundedCornerShape(8.dp),
            ) {
                Icon(Icons.Default.PowerSettingsNew, null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(4.dp))
                Text("Įjungti")
            }
        }
    }
}

@Composable
private fun QuickWakeCard(onExpand: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = ApsaColors.Card),
        shape = RoundedCornerShape(12.dp),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Be sąrašo – tik MAC adresas", color = ApsaColors.Muted, fontSize = 13.sp)
            Spacer(Modifier.height(8.dp))
            Button(
                onClick = onExpand,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = ApsaColors.Accent),
            ) { Text("Greitas įjungimas") }
        }
    }
}

@Composable
private fun ComputerEditorDialog(
    computer: Computer,
    suggestedBroadcast: String,
    onDismiss: () -> Unit,
    onSave: (Computer) -> Unit,
) {
    var name by remember(computer.id) { mutableStateOf(computer.name) }
    var mac by remember(computer.id) { mutableStateOf(computer.mac) }
    var broadcast by remember(computer.id) { mutableStateOf(computer.broadcast) }
    var port by remember(computer.id) { mutableStateOf(computer.port.toString()) }
    var description by remember(computer.id) { mutableStateOf(computer.description) }

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = ApsaColors.Card,
        title = {
            Text(
                if (computer.name.isBlank()) "Naujas kompiuteris" else "Redaguoti",
                color = ApsaColors.Text,
            )
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                ApsaTextField(name, { name = it }, "Pavadinimas")
                ApsaTextField(mac, { mac = it }, "MAC adresas")
                ApsaTextField(broadcast, { broadcast = it }, "Broadcast IP")
                TextButton(onClick = { broadcast = suggestedBroadcast }) {
                    Text("Naudoti: $suggestedBroadcast", color = ApsaColors.Accent, fontSize = 12.sp)
                }
                ApsaTextField(port, { port = it }, "UDP prievadas (9)")
                ApsaTextField(description, { description = it }, "Aprašymas")
            }
        },
        confirmButton = {
            TextButton(onClick = {
                onSave(
                    computer.copy(
                        name = name.trim(),
                        mac = mac.trim(),
                        broadcast = broadcast.trim().ifBlank { suggestedBroadcast },
                        port = port.toIntOrNull() ?: 9,
                        description = description.trim(),
                    ),
                )
            }) { Text("Išsaugoti", color = ApsaColors.Accent) }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Atšaukti", color = ApsaColors.Muted) }
        },
    )
}

@Composable
private fun SettingsDialog(
    repeats: Int,
    onDismiss: () -> Unit,
    onSave: (Int) -> Unit,
) {
    var value by remember { mutableFloatStateOf(repeats.toFloat()) }

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = ApsaColors.Card,
        title = { Text("Nustatymai", color = ApsaColors.Text) },
        text = {
            Column {
                Text(
                    "Magic packet pakartojimai: ${value.roundToInt()}",
                    color = ApsaColors.Muted,
                )
                Slider(
                    value = value,
                    onValueChange = { value = it },
                    valueRange = 1f..10f,
                    steps = 8,
                )
                Text(
                    "Daugiau pakartojimų = patikimesnis įjungimas",
                    color = ApsaColors.Muted,
                    fontSize = 12.sp,
                )
            }
        },
        confirmButton = {
            TextButton(onClick = {
                onSave(value.roundToInt())
                onDismiss()
            }) { Text("Išsaugoti", color = ApsaColors.Accent) }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Atšaukti", color = ApsaColors.Muted) }
        },
    )
}

@Composable
private fun ApsaTextField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label) },
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
        colors = OutlinedTextFieldDefaults.colors(
            focusedTextColor = ApsaColors.Text,
            unfocusedTextColor = ApsaColors.Text,
            focusedBorderColor = ApsaColors.Accent,
            unfocusedBorderColor = ApsaColors.Border,
            focusedLabelColor = ApsaColors.Accent,
            unfocusedLabelColor = ApsaColors.Muted,
            cursorColor = ApsaColors.Accent,
        ),
    )
}
