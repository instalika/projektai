package com.instalika.apsapower.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColorScheme = darkColorScheme(
    primary = ApsaColors.Accent,
    onPrimary = Color.White,
    secondary = ApsaColors.AccentHover,
    background = ApsaColors.Background,
    surface = ApsaColors.Card,
    onBackground = ApsaColors.Text,
    onSurface = ApsaColors.Text,
    error = ApsaColors.Error,
)

@Composable
fun ApsaPowerTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        content = content,
    )
}
