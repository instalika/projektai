package com.instalika.apsapower.data

import kotlinx.serialization.Serializable

@Serializable
data class Computer(
    val id: String,
    val name: String,
    val mac: String,
    val broadcast: String = "255.255.255.255",
    val description: String = "",
)
