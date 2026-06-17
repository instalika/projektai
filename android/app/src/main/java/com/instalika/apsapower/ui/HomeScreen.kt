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
import androidx.compose.material.icons.filled.PowerSettingsNew
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(viewModel: MainViewModel) {
    val computers by viewModel.computers.collectAsState()
    val message by viewModel.message.collectAsState()
    val editor by viewModel.showEditor.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    var showQuickWake by remember { mutableStateOf(false) }
    var quickMac by remember { mutableStateOf("") }
    var quickBroadcast by remember { mutableStateOf("255.255.255.255") }

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
                            "APSA Power",
                            fontWeight = FontWeight.Bold,
                            color = ApsaColors.Accent,
                            fontSize = 20.sp,
                        )
                        Text(
                            "Instalika",
                            color = ApsaColors.Muted,
                            fontSize = 13.sp,
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = ApsaColors.Background,
                ),
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
                Text(
                    "Kompiuterių įjungimas per LAN",
                    color = ApsaColors.Muted,
                    fontSize = 14.sp,
                    modifier = Modifier.padding(bottom = 4.dp),
                )
            }

            if (computers.isEmpty()) {
                item {
                    EmptyCard()
                }
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
                Spacer(modifier = Modifier.height(4.dp))
                QuickWakeCard(
                    onExpand = { showQuickWake = true },
                )
                Spacer(modifier = Modifier.height(80.dp))
            }
        }
    }

    editor?.let { computer ->
        ComputerEditorDialog(
            computer = computer,
            onDismiss = { viewModel.closeEditor() },
            onSave = { viewModel.saveComputer(it) },
        )
    }

    if (showQuickWake) {
        AlertDialog(
            onDismissRequest = { showQuickWake = false },
            containerColor = ApsaColors.Card,
            title = { Text("Įjungti pagal MAC", color = ApsaColors.Text) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    ApsaTextField(quickMac, { quickMac = it }, "MAC adresas (AA:BB:CC:DD:EE:FF)")
                    ApsaTextField(quickBroadcast, { quickBroadcast = it }, "Broadcast IP")
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.wakeByMac(quickMac, quickBroadcast)
                    showQuickWake = false
                }) {
                    Text("Siųsti", color = ApsaColors.Accent)
                }
            },
            dismissButton = {
                TextButton(onClick = { showQuickWake = false }) {
                    Text("Atšaukti", color = ApsaColors.Muted)
                }
            },
        )
    }
}

@Composable
private fun EmptyCard() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = ApsaColors.Card),
        shape = RoundedCornerShape(12.dp),
    ) {
        Text(
            "Nėra kompiuterių. Paspauskite + ir pridėkite.",
            color = ApsaColors.Muted,
            modifier = Modifier.padding(20.dp),
        )
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
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(computer.name, fontWeight = FontWeight.SemiBold, color = ApsaColors.Text)
                Text(
                    computer.mac,
                    color = ApsaColors.Muted,
                    fontFamily = FontFamily.Monospace,
                    fontSize = 13.sp,
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
                Icon(
                    Icons.Default.PowerSettingsNew,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp),
                )
                Spacer(modifier = Modifier.width(4.dp))
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
            Text("Greitas įjungimas", color = ApsaColors.Muted, fontSize = 13.sp)
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = onExpand,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = ApsaColors.Accent),
            ) {
                Text("Įvesti MAC adresą")
            }
        }
    }
}

@Composable
private fun ComputerEditorDialog(
    computer: Computer,
    onDismiss: () -> Unit,
    onSave: (Computer) -> Unit,
) {
    var name by remember(computer.id) { mutableStateOf(computer.name) }
    var mac by remember(computer.id) { mutableStateOf(computer.mac) }
    var broadcast by remember(computer.id) { mutableStateOf(computer.broadcast) }
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
                ApsaTextField(description, { description = it }, "Aprašymas (nebūtina)")
            }
        },
        confirmButton = {
            TextButton(onClick = {
                onSave(
                    computer.copy(
                        name = name.trim(),
                        mac = mac.trim(),
                        broadcast = broadcast.trim().ifBlank { "255.255.255.255" },
                        description = description.trim(),
                    ),
                )
            }) {
                Text("Išsaugoti", color = ApsaColors.Accent)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Atšaukti", color = ApsaColors.Muted)
            }
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
