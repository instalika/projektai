package com.instalika.apsapower

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.instalika.apsapower.ui.ApsaPowerTheme
import com.instalika.apsapower.ui.HomeScreen
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    private var vmRef: MainViewModel? = null

    private val importLauncher = registerForActivityResult(
        ActivityResultContracts.OpenDocument(),
    ) { uri ->
        uri?.let { vmRef?.importFromUri(it) }
    }

    private val exportLauncher = registerForActivityResult(
        ActivityResultContracts.CreateDocument("application/json"),
    ) { uri ->
        uri?.let { vmRef?.writeExportToUri(it) }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            ApsaPowerTheme {
                val vm: MainViewModel = viewModel()
                vmRef = vm
                HomeScreen(
                    viewModel = vm,
                    onImport = {
                        importLauncher.launch(arrayOf("application/json", "text/*", "*/*"))
                    },
                    onExport = {
                        exportLauncher.launch("instalika-power-computers.json")
                    },
                    onShare = {
                        lifecycleScope.launch {
                            val intent = vm.buildShareIntent()
                            startActivity(Intent.createChooser(intent, "Eksportuoti"))
                        }
                    },
                )
            }
        }
    }
}
