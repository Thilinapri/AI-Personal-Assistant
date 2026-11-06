package com.echomind.reminder.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.echomind.reminder.LatestReminder
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale


private val PageBackground =
    Color(0xFFF6F7FB)

private val Navy =
    Color(0xFF0F172A)

private val Indigo =
    Color(0xFF5B4CF0)

private val IndigoSoft =
    Color(0xFFEEF0FF)

private val Green =
    Color(0xFF059669)

private val GreenSoft =
    Color(0xFFECFDF5)

private val Slate =
    Color(0xFF64748B)

private val Border =
    Color(0xFFE2E8F0)


@Composable
fun EchoMindHomeScreen(
    notificationsEnabled: Boolean,
    latestReminder: LatestReminder?,
    onOpenNotificationSettings: () -> Unit,
) {

    Surface(
        modifier =
            Modifier.fillMaxSize(),
        color =
            PageBackground,
    ) {

        Column(
            modifier =
                Modifier
                    .fillMaxSize()
                    .padding(
                        horizontal =
                            20.dp,
                        vertical =
                            24.dp,
                    ),
        ) {

            Header()

            Spacer(
                modifier =
                    Modifier.height(
                        24.dp,
                    ),
            )

            StatusCard(
                notificationsEnabled =
                    notificationsEnabled,
            )

            Spacer(
                modifier =
                    Modifier.height(
                        16.dp,
                    ),
            )

            NotificationStatusCard(
                notificationsEnabled =
                    notificationsEnabled,

                onOpenNotificationSettings =
                    onOpenNotificationSettings,
            )

            Spacer(
                modifier =
                    Modifier.height(
                        16.dp,
                    ),
            )

            LastReminderCard(
                latestReminder =
                    latestReminder,
            )

            Spacer(
                modifier =
                    Modifier.weight(
                        1f
                    ),
            )

            Footer()
        }
    }
}


@Composable
private fun Header() {

    Row(
        modifier =
            Modifier.fillMaxWidth(),
        verticalAlignment =
            Alignment.CenterVertically,
    ) {

        Box(
            modifier =
                Modifier
                    .size(
                        52.dp
                    )
                    .background(
                        color =
                            Indigo,
                        shape =
                            RoundedCornerShape(
                                16.dp
                            ),
                    ),
            contentAlignment =
                Alignment.Center,
        ) {

            Text(
                text =
                    "✦",
                color =
                    Color.White,
                fontSize =
                    26.sp,
                fontWeight =
                    FontWeight.Bold,
            )
        }


        Column(
            modifier =
                Modifier.padding(
                    start =
                        14.dp,
                ),
        ) {

            Row(
                verticalAlignment =
                    Alignment.CenterVertically,
            ) {

                Text(
                    text =
                        "EchoMind",
                    color =
                        Navy,
                    fontSize =
                        23.sp,
                    fontWeight =
                        FontWeight.Bold,
                )

                Text(
                    text =
                        "  AI",
                    color =
                        Indigo,
                    fontSize =
                        11.sp,
                    fontWeight =
                        FontWeight.Bold,
                )
            }


            Text(
                text =
                    "Reminder Companion",
                color =
                    Slate,
                fontSize =
                    13.sp,
            )
        }
    }
}


@Composable
private fun StatusCard(
    notificationsEnabled: Boolean,
) {

    Card(
        modifier =
            Modifier.fillMaxWidth(),
        shape =
            RoundedCornerShape(
                22.dp
            ),
        colors =
            CardDefaults.cardColors(
                containerColor =
                    Color.White,
            ),
        elevation =
            CardDefaults.cardElevation(
                defaultElevation =
                    2.dp,
            ),
    ) {

        Column(
            modifier =
                Modifier.padding(
                    20.dp,
                ),
        ) {

            Text(
                text =
                    "EchoMind Status",
                color =
                    Slate,
                fontSize =
                    12.sp,
                fontWeight =
                    FontWeight.SemiBold,
            )

            Spacer(
                modifier =
                    Modifier.height(
                        14.dp,
                    ),
            )


            Row(
                modifier =
                    Modifier.fillMaxWidth(),
                verticalAlignment =
                    Alignment.CenterVertically,
                horizontalArrangement =
                    Arrangement.SpaceBetween,
            ) {

                Column {

                    Text(
                        text =
                            if (notificationsEnabled) {
                                "Ready"
                            } else {
                                "Notifications Off"
                            },
                        color =
                            Navy,
                        fontSize =
                            25.sp,
                        fontWeight =
                            FontWeight.Bold,
                    )

                    Text(
                        text =
                            if (notificationsEnabled) {
                                "Notifications are enabled."
                            } else {
                                "Enable notifications to receive reminders."
                            },
                        color =
                            Slate,
                        fontSize =
                            12.sp,
                    )
                }


                Box(
                    modifier =
                        Modifier
                            .size(
                                46.dp
                            )
                            .background(
                                color =
                                    if (notificationsEnabled) GreenSoft else Color(0xFFFFF7ED),
                                shape =
                                    CircleShape,
                            ),
                    contentAlignment =
                        Alignment.Center,
                ) {

                    Box(
                        modifier =
                            Modifier
                                .size(
                                    12.dp
                                )
                                .background(
                                    color =
                                        if (notificationsEnabled) Green else Color(0xFFD97706),
                                    shape =
                                        CircleShape,
                                ),
                    )
                }
            }


            Spacer(
                modifier =
                    Modifier.height(
                        18.dp,
                    ),
            )


            Row(
                verticalAlignment =
                    Alignment.CenterVertically,
            ) {

                Box(
                    modifier =
                        Modifier
                            .size(
                                8.dp
                            )
                            .background(
                                color =
                                    if (notificationsEnabled) Green else Color(0xFFD97706),
                                shape =
                                    CircleShape,
                            ),
                )


                Text(
                    modifier =
                        Modifier.padding(
                            start =
                                8.dp,
                        ),
                    text =
                        if (
                            notificationsEnabled
                        ) {
                            "Notification service active"
                        } else {
                            "Notifications require attention"
                        },
                    color =
                        if (
                            notificationsEnabled
                        ) {
                            Green
                        } else {
                            Color(
                                0xFFD97706
                            )
                        },
                    fontSize =
                        12.sp,
                    fontWeight =
                        FontWeight.SemiBold,
                )
            }
        }
    }
}


@Composable
private fun NotificationStatusCard(
    notificationsEnabled: Boolean,
    onOpenNotificationSettings: () -> Unit,
) {

    Card(
        modifier =
            Modifier.fillMaxWidth(),
        shape =
            RoundedCornerShape(
                22.dp
            ),
        colors =
            CardDefaults.cardColors(
                containerColor =
                    Color.White,
            ),
        elevation =
            CardDefaults.cardElevation(
                defaultElevation =
                    1.dp,
            ),
    ) {

        Column(
            modifier =
                Modifier.padding(
                    20.dp,
                ),
        ) {

            Row(
                modifier =
                    Modifier.fillMaxWidth(),
                verticalAlignment =
                    Alignment.CenterVertically,
                horizontalArrangement =
                    Arrangement.SpaceBetween,
            ) {

                Column(
                    modifier =
                        Modifier.weight(
                            1f
                        ),
                ) {

                    Text(
                        text =
                            "Reminder Notifications",
                        color =
                            Navy,
                        fontSize =
                            16.sp,
                        fontWeight =
                            FontWeight.Bold,
                    )

                    Spacer(
                        modifier =
                            Modifier.height(
                                4.dp,
                            ),
                    )

                    Text(
                        text =
                            if (
                                notificationsEnabled
                            ) {
                                "Notifications are enabled on this device."
                            } else {
                                "Enable notifications so EchoMind can alert you."
                            },
                        color =
                            Slate,
                        fontSize =
                            12.sp,
                    )
                }


                Box(
                    modifier =
                        Modifier
                            .padding(
                                start =
                                    12.dp,
                            )
                            .background(
                                color =
                                    if (
                                        notificationsEnabled
                                    ) {
                                        GreenSoft
                                    } else {
                                        IndigoSoft
                                    },
                                shape =
                                    RoundedCornerShape(
                                        999.dp
                                    ),
                            )
                            .padding(
                                horizontal =
                                    12.dp,
                                vertical =
                                    7.dp,
                            ),
                ) {

                    Text(
                        text =
                            if (
                                notificationsEnabled
                            ) {
                                "ENABLED"
                            } else {
                                "CHECK"
                            },
                        color =
                            if (
                                notificationsEnabled
                            ) {
                                Green
                            } else {
                                Indigo
                            },
                        fontSize =
                            10.sp,
                        fontWeight =
                            FontWeight.Bold,
                    )
                }
            }


            Spacer(
                modifier =
                    Modifier.height(
                        16.dp,
                    ),
            )


            Button(
                modifier =
                    Modifier.fillMaxWidth(),
                onClick =
                    onOpenNotificationSettings,
                shape =
                    RoundedCornerShape(
                        14.dp
                    ),
                colors =
                    ButtonDefaults.buttonColors(
                        containerColor =
                            IndigoSoft,
                        contentColor =
                            Indigo,
                    ),
            ) {

                Text(
                    text =
                        "Notification Settings",
                    fontWeight =
                        FontWeight.Bold,
                    fontSize =
                        12.sp,
                )
            }
        }
    }
}


@Composable
private fun LastReminderCard(
    latestReminder: LatestReminder?,
) {

    Card(
        modifier =
            Modifier.fillMaxWidth(),
        shape =
            RoundedCornerShape(
                22.dp
            ),
        colors =
            CardDefaults.cardColors(
                containerColor =
                    Color.White,
            ),
        elevation =
            CardDefaults.cardElevation(
                defaultElevation =
                    1.dp,
            ),
    ) {

        Column(
            modifier =
                Modifier.padding(
                    20.dp,
                ),
        ) {

            Text(
                text =
                    "Latest Reminder",
                color =
                    Navy,
                fontSize =
                    16.sp,
                fontWeight =
                    FontWeight.Bold,
            )


            Spacer(
                modifier =
                    Modifier.height(
                        18.dp,
                    ),
            )


            if (
                latestReminder ==
                null
            ) {

                EmptyReminderState()

            } else {

                ReminderContent(
                    reminder =
                        latestReminder,
                )
            }
        }
    }
}


@Composable
private fun EmptyReminderState() {

    Box(
        modifier =
            Modifier
                .fillMaxWidth()
                .background(
                    color =
                        PageBackground,
                    shape =
                        RoundedCornerShape(
                            16.dp
                        ),
                )
                .padding(
                    20.dp,
                ),
        contentAlignment =
            Alignment.Center,
    ) {

        Column(
            horizontalAlignment =
                Alignment.CenterHorizontally,
        ) {

            Box(
                modifier =
                    Modifier
                        .size(
                            40.dp
                        )
                        .background(
                            color =
                                IndigoSoft,
                            shape =
                                CircleShape,
                        ),
                contentAlignment =
                    Alignment.Center,
            ) {

                Text(
                    text =
                        "●",
                    color =
                        Indigo,
                    fontSize =
                        14.sp,
                )
            }


            Spacer(
                modifier =
                    Modifier.height(
                        12.dp,
                    ),
            )


            Text(
                text =
                    "No reminder received yet",
                color =
                    Navy,
                fontSize =
                    14.sp,
                fontWeight =
                    FontWeight.SemiBold,
            )


            Spacer(
                modifier =
                    Modifier.height(
                        4.dp,
                    ),
            )


            Text(
                text =
                    "Your latest EchoMind reminder will appear here.",
                color =
                    Slate,
                fontSize =
                    11.sp,
                textAlign =
                    TextAlign.Center,
            )
        }
    }
}


@Composable
private fun ReminderContent(
    reminder: LatestReminder,
) {

    Column(
        modifier =
            Modifier
                .fillMaxWidth()
                .background(
                    color =
                        PageBackground,
                    shape =
                        RoundedCornerShape(
                            16.dp
                        ),
                )
                .padding(
                    18.dp,
                ),
    ) {

        Row(
            verticalAlignment =
                Alignment.CenterVertically,
        ) {

            Box(
                modifier =
                    Modifier
                        .size(
                            10.dp
                        )
                        .background(
                            color =
                                Green,
                            shape =
                                CircleShape,
                        ),
            )


            Text(
                modifier =
                    Modifier.padding(
                        start =
                            8.dp,
                    ),
                text =
                    "RECEIVED",
                color =
                    Green,
                fontSize =
                    10.sp,
                fontWeight =
                    FontWeight.Bold,
            )
        }


        Spacer(
            modifier =
                Modifier.height(
                    12.dp,
                ),
        )


        Text(
            text =
                reminder.title,
            color =
                Navy,
            fontSize =
                16.sp,
            fontWeight =
                FontWeight.Bold,
        )


        Spacer(
            modifier =
                Modifier.height(
                    6.dp,
                ),
        )


        Text(
            text =
                reminder.body,
            color =
                Slate,
            fontSize =
                12.sp,
        )


        Spacer(
            modifier =
                Modifier.height(
                    14.dp,
                ),
        )


        Text(
            text =
                "Received ${formatReceivedTime(reminder.receivedAt)}",
            color =
                Slate,
            fontSize =
                10.sp,
            fontWeight =
                FontWeight.Medium,
        )
    }
}


private fun formatReceivedTime(
    timestamp: Long,
): String {

    if (
        timestamp <= 0
    ) {
        return "recently"
    }


    val formatter =
        SimpleDateFormat(
            "MMM d, yyyy · h:mm a",
            Locale.getDefault(),
        )


    return formatter.format(
        Date(
            timestamp
        )
    )
}


@Composable
private fun Footer() {

    Column(
        modifier =
            Modifier.fillMaxWidth(),
        horizontalAlignment =
            Alignment.CenterHorizontally,
    ) {

        Box(
            modifier =
                Modifier
                    .fillMaxWidth()
                    .height(
                        1.dp
                    )
                    .background(
                        Border,
                    ),
        )


        Spacer(
            modifier =
                Modifier.height(
                    14.dp,
                ),
        )


        Text(
            text =
                "EchoMind · Remember what matters.",
            color =
                Slate,
            fontSize =
                11.sp,
            textAlign =
                TextAlign.Center,
        )
    }
}