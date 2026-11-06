package com.echomind.reminder

import android.Manifest
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.mutableStateOf
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import com.echomind.reminder.ui.EchoMindHomeScreen
import com.google.firebase.messaging.FirebaseMessaging


class MainActivity :
    ComponentActivity() {


    private val notificationsEnabled =
        mutableStateOf(false)


    private val latestReminder =
        mutableStateOf<LatestReminder?>(
            null
        )


    private lateinit var reminderPreferences:
        SharedPreferences


    private val preferenceListener =
        SharedPreferences
            .OnSharedPreferenceChangeListener {
                    _,
                    _ ->

                loadLatestReminder()
            }


    private val requestNotificationPermission =
        registerForActivityResult(
            ActivityResultContracts
                .RequestPermission()
        ) {

            updateNotificationStatus()
        }


    override fun onCreate(
        savedInstanceState: Bundle?
    ) {

        super.onCreate(
            savedInstanceState
        )


        reminderPreferences =
            getSharedPreferences(
                ReminderStorage.PREFS_NAME,
                MODE_PRIVATE,
            )


        reminderPreferences
            .registerOnSharedPreferenceChangeListener(
                preferenceListener
            )


        loadLatestReminder()

        updateNotificationStatus()

        requestNotificationPermissionIfNeeded()

        logFirebaseToken()


        setContent {

            MaterialTheme {

                Surface {

                    EchoMindHomeScreen(
                        notificationsEnabled =
                            notificationsEnabled.value,

                        latestReminder =
                            latestReminder.value,

                        onOpenNotificationSettings = {
                            openNotificationSettings()
                        },
                    )
                }
            }
        }
    }


    override fun onResume() {

        super.onResume()

        updateNotificationStatus()

        loadLatestReminder()
    }


    override fun onDestroy() {

        reminderPreferences
            .unregisterOnSharedPreferenceChangeListener(
                preferenceListener
            )

        super.onDestroy()
    }


    private fun loadLatestReminder() {

        latestReminder.value =
            ReminderStorage.load(
                this
            )
    }


    private fun updateNotificationStatus() {
        notificationsEnabled.value =
            NotificationManagerCompat
                .from(this)
                .areNotificationsEnabled()
    }


    private fun requestNotificationPermissionIfNeeded() {

        if (
            Build.VERSION.SDK_INT >=
            Build.VERSION_CODES.TIRAMISU
        ) {

            val permission =
                ContextCompat
                    .checkSelfPermission(
                        this,
                        Manifest.permission
                            .POST_NOTIFICATIONS,
                    )


            if (
                permission !=
                PackageManager
                    .PERMISSION_GRANTED
            ) {

                requestNotificationPermission
                    .launch(
                        Manifest.permission
                            .POST_NOTIFICATIONS
                    )
            }
        }
    }


    private fun openNotificationSettings() {

        val intent =
            Intent(
                Settings
                    .ACTION_APPLICATION_DETAILS_SETTINGS
            ).apply {

                data =
                    Uri.fromParts(
                        "package",
                        packageName,
                        null,
                    )
            }


        startActivity(
            intent
        )
    }


    private fun logFirebaseToken() {

        FirebaseMessaging
            .getInstance()
            .token
            .addOnCompleteListener {
                    task ->

                if (
                    !task.isSuccessful
                ) {

                    Log.w(
                        "EchoMindFCM",
                        "Unable to get FCM token.",
                        task.exception,
                    )

                    return@addOnCompleteListener
                }


                Log.d(
                    "EchoMindFCM",
                    "FCM token is available.",
                )
            }
    }
}