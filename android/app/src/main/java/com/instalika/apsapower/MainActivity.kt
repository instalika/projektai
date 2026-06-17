package com.instalika.apsapower

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.viewmodel.compose.viewModel
import com.instalika.apsapower.ui.ApsaPowerTheme
import com.instalika.apsapower.ui.HomeScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            ApsaPowerTheme {
                val vm: MainViewModel = viewModel()
                HomeScreen(viewModel = vm)
            }
        }
    }
}
