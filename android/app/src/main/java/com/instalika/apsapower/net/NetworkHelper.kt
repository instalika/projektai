package com.instalika.apsapower.net

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.wifi.WifiManager

object NetworkHelper {
    fun getSubnetBroadcast(context: Context): String? {
        val wifiManager = context.applicationContext.getSystemService(WifiManager::class.java)
            ?: return null
        @Suppress("DEPRECATION")
        val dhcp = wifiManager.dhcpInfo ?: return null
        if (dhcp.ipAddress == 0) return null

        val ip = dhcp.ipAddress
        val mask = dhcp.netmask
        val broadcast = (ip and mask) or mask.inv()
        return intToIp(broadcast)
    }

    fun isOnWifi(context: Context): Boolean {
        val cm = context.getSystemService(ConnectivityManager::class.java) ?: return false
        val network = cm.activeNetwork ?: return false
        val caps = cm.getNetworkCapabilities(network) ?: return false
        return caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
    }

    private fun intToIp(value: Int): String {
        return "${value and 0xFF}.${value shr 8 and 0xFF}.${value shr 16 and 0xFF}.${value shr 24 and 0xFF}"
    }
}
