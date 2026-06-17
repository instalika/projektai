package com.instalika.apsapower.wol

import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.util.regex.Pattern

object WolSender {
    private val MAC_PATTERN = Pattern.compile("^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
    const val DEFAULT_PORT = 9
    const val DEFAULT_REPEATS = 3
    const val REPEAT_DELAY_MS = 100L

    fun isValidMac(mac: String): Boolean = MAC_PATTERN.matcher(mac.trim()).matches()

    fun normalizeMac(mac: String): String =
        mac.trim().replace('-', ':').uppercase()

    fun sendMagicPacket(
        mac: String,
        broadcast: String = "255.255.255.255",
        port: Int = DEFAULT_PORT,
        repeats: Int = DEFAULT_REPEATS,
    ) {
        val normalized = normalizeMac(mac)
        if (!isValidMac(normalized)) {
            throw IllegalArgumentException("Neteisingas MAC adresas: $mac")
        }
        if (port !in 1..65535) {
            throw IllegalArgumentException("Neteisingas prievadas: $port")
        }

        val macBytes = normalized.split(":").map { it.toInt(16).toByte() }.toByteArray()
        val packet = ByteArray(102) { index ->
            when {
                index < 6 -> 0xFF.toByte()
                else -> macBytes[(index - 6) % 6]
            }
        }

        val count = repeats.coerceIn(1, 10)
        DatagramSocket().use { socket ->
            socket.broadcast = true
            val address = InetAddress.getByName(broadcast)
            repeat(count) { attempt ->
                val datagram = DatagramPacket(packet, packet.size, address, port)
                socket.send(datagram)
                if (attempt < count - 1) {
                    Thread.sleep(REPEAT_DELAY_MS)
                }
            }
        }
    }
}
