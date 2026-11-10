package com.echomind.reminder

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage


class EchoMindFirebaseMessagingService :
    FirebaseMessagingService() {


    override fun onNewToken(
        token: String
    ) {

        super.onNewToken(token)

        Log.d(
            TAG,
            "FCM token refreshed."
        )

        // Later this token can be
        // registered with the backend automatically.
    }


    override fun onMessageReceived(
        remoteMessage: RemoteMessage
    ) {

        super.onMessageReceived(
            remoteMessage
        )

        Log.d(
            TAG,
            "FCM message received"
        )


        val title =
            remoteMessage
                .notification
                ?.title
                ?: remoteMessage
                    .data["title"]
                ?: "EchoMind Reminder"


        val body =
            remoteMessage
                .notification
                ?.body
                ?: remoteMessage
                    .data["body"]
                ?: "You have an upcoming reminder."


        ReminderStorage.save(
            context = this,
            title = title,
            body = body,
        )


        showNotification(
            title = title,
            body = body
        )
    }


    private fun showNotification(
        title: String,
        body: String
    ) {

        val notificationManager =
            getSystemService(
                NotificationManager::class.java
            )


        if (
            Build.VERSION.SDK_INT
            >= Build.VERSION_CODES.O
        ) {

            val channel =
                NotificationChannel(
                    CHANNEL_ID,
                    "EchoMind Reminders",
                    NotificationManager
                        .IMPORTANCE_HIGH
                ).apply {

                    description =
                        "Time-sensitive reminders from EchoMind"

                    enableVibration(true)

                    setShowBadge(true)
                }


            notificationManager
                .createNotificationChannel(
                    channel
                )
        }


        val intent =
            Intent(
                this,
                MainActivity::class.java
            ).apply {

                flags =
                    Intent.FLAG_ACTIVITY_CLEAR_TOP or
                    Intent.FLAG_ACTIVITY_SINGLE_TOP
            }


        val pendingIntent =
            PendingIntent.getActivity(
                this,
                0,
                intent,
                PendingIntent
                    .FLAG_UPDATE_CURRENT or
                    PendingIntent
                        .FLAG_IMMUTABLE
            )


        val notification =
            NotificationCompat
                .Builder(
                    this,
                    CHANNEL_ID
                )
                .setSmallIcon(
                    android.R.drawable
                        .ic_dialog_info
                )
                .setContentTitle(
                    title
                )
                .setContentText(
                    body
                )
                .setStyle(
                    NotificationCompat
                        .BigTextStyle()
                        .bigText(
                            body
                        )
                )
                .setPriority(
                    NotificationCompat
                        .PRIORITY_HIGH
                )
                .setCategory(
                    NotificationCompat
                        .CATEGORY_REMINDER
                )
                .setDefaults(
                    NotificationCompat
                        .DEFAULT_ALL
                )
                .setAutoCancel(
                    true
                )
                .setContentIntent(
                    pendingIntent
                )
                .build()


        notificationManager
            .notify(
                System
                    .currentTimeMillis()
                    .toInt(),

                notification
            )
    }


    companion object {

        private const val TAG =
            "EchoMindFCM"

        private const val CHANNEL_ID =
            "echomind_reminders_v2"
    }
}