package com.echomind.reminder

import android.content.Context


data class LatestReminder(
    val title: String,
    val body: String,
    val receivedAt: Long,
)


object ReminderStorage {

    const val PREFS_NAME =
        "echomind_reminder_storage"

    private const val KEY_TITLE =
        "latest_reminder_title"

    private const val KEY_BODY =
        "latest_reminder_body"

    private const val KEY_RECEIVED_AT =
        "latest_reminder_received_at"


    fun save(
        context: Context,
        title: String,
        body: String,
    ) {

        context
            .getSharedPreferences(
                PREFS_NAME,
                Context.MODE_PRIVATE,
            )
            .edit()
            .putString(
                KEY_TITLE,
                title,
            )
            .putString(
                KEY_BODY,
                body,
            )
            .putLong(
                KEY_RECEIVED_AT,
                System.currentTimeMillis(),
            )
            .apply()
    }


    fun load(
        context: Context,
    ): LatestReminder? {

        val preferences =
            context.getSharedPreferences(
                PREFS_NAME,
                Context.MODE_PRIVATE,
            )

        val title =
            preferences.getString(
                KEY_TITLE,
                null,
            )
                ?: return null

        val body =
            preferences.getString(
                KEY_BODY,
                "",
            )
                ?: ""

        val receivedAt =
            preferences.getLong(
                KEY_RECEIVED_AT,
                0L,
            )

        return LatestReminder(
            title = title,
            body = body,
            receivedAt = receivedAt,
        )
    }
}