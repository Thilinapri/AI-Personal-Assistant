import { createClient } from "npm:@supabase/supabase-js@2.117.1";
import { JWT } from "npm:google-auth-library@11.1.0";

const FIREBASE_SCOPE =
  "https://www.googleapis.com/auth/firebase.messaging";


function getSupabaseSecretKey(): string {
  const legacyKey =
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

  if (legacyKey) {
    return legacyKey;
  }

  const rawKeys =
    Deno.env.get("SUPABASE_SECRET_KEYS");

  if (!rawKeys) {
    throw new Error(
      "Supabase secret key is unavailable."
    );
  }

  const keys = JSON.parse(rawKeys);

  const secretKey =
    keys.default ??
    Object.values(keys)[0];

  if (typeof secretKey !== "string") {
    throw new Error(
      "No usable Supabase secret key found."
    );
  }

  return secretKey;
}


async function getFirebaseAccessToken(
  serviceAccount: {
    client_email: string;
    private_key: string;
  },
): Promise<string> {

  const authClient = new JWT({
    email: serviceAccount.client_email,
    key: serviceAccount.private_key,
    scopes: [FIREBASE_SCOPE],
  });

  const credentials =
    await authClient.authorize();

  if (!credentials.access_token) {
    throw new Error(
      "Firebase access token was not generated."
    );
  }

  return credentials.access_token;
}


Deno.serve(async (request) => {

  if (request.method !== "POST") {
    return Response.json(
      { error: "Method not allowed" },
      { status: 405 },
    );
  }


  // ---------------------------------
  // Verify EchoMind Cron secret
  // ---------------------------------

  const expectedSecret =
    Deno.env.get("ECHOMIND_CRON_SECRET");

  const suppliedSecret =
    request.headers.get(
      "x-echomind-cron-secret"
    );

  if (
    !expectedSecret ||
    suppliedSecret !== expectedSecret
  ) {
    return Response.json(
      { error: "Unauthorized" },
      { status: 401 },
    );
  }


  try {

    // ---------------------------------
    // Environment
    // ---------------------------------

    const supabaseUrl =
      Deno.env.get("SUPABASE_URL");

    const firebaseJson =
      Deno.env.get(
        "FIREBASE_SERVICE_ACCOUNT_JSON"
      );

    const fcmToken =
      Deno.env.get("ECHOMIND_FCM_TOKEN");

    if (!supabaseUrl) {
      throw new Error(
        "SUPABASE_URL is unavailable."
      );
    }

    if (!firebaseJson) {
      throw new Error(
        "Firebase service account secret is missing."
      );
    }

    if (!fcmToken) {
      throw new Error(
        "FCM device token is missing."
      );
    }

    const serviceAccount =
      JSON.parse(firebaseJson);

    const projectId =
      serviceAccount.project_id;

    if (!projectId) {
      throw new Error(
        "Firebase project_id is missing."
      );
    }


    // ---------------------------------
    // Supabase Admin Client
    // ---------------------------------

    const supabase = createClient(
      supabaseUrl,
      getSupabaseSecretKey(),
      {
        auth: {
          persistSession: false,
          autoRefreshToken: false,
        },
      },
    );


    // ---------------------------------
    // Find Due Reminders
    // ---------------------------------

    const now = new Date().toISOString();

    const {
      data: reminders,
      error: reminderError,
    } = await supabase
      .from("cloud_reminders")
      .select(`
        id,
        notification_title,
        notification_body,
        reminder_time,
        status
      `)
      .eq("status", "pending")
      .lte("reminder_time", now)
      .order("reminder_time", {
        ascending: true,
      })
      .limit(20);

    if (reminderError) {
      throw reminderError;
    }

    if (!reminders || reminders.length === 0) {
      return Response.json({
        ok: true,
        checkedAt: now,
        due: 0,
        sent: 0,
        failed: 0,
      });
    }


    // ---------------------------------
    // Firebase OAuth Token
    // ---------------------------------

    const accessToken =
      await getFirebaseAccessToken(
        serviceAccount
      );

    let sentCount = 0;
    let failedCount = 0;


    // ---------------------------------
    // Send Each Reminder
    // ---------------------------------

    for (const reminder of reminders) {

      try {

        const notificationTitle =
          reminder.notification_title
          ?? "EchoMind Reminder";

        const notificationBody =
          reminder.notification_body
          ?? "You have an upcoming reminder.";


        // ---------------------------------
        // Data-only FCM message
        //
        // Do not include "notification".
        // Android's onMessageReceived()
        // must process the message.
        // ---------------------------------

        const firebaseMessage = {
          message: {
            token: fcmToken,

            data: {
              title: notificationTitle,
              body: notificationBody,
              cloud_reminder_id:
                String(reminder.id),
            },

            android: {
              priority: "HIGH",
            },
          },
        };


        const response = await fetch(
          `https://fcm.googleapis.com/v1/projects/${projectId}/messages:send`,
          {
            method: "POST",

            headers: {
              Authorization:
                `Bearer ${accessToken}`,

              "Content-Type":
                "application/json",
            },

            body: JSON.stringify(
              firebaseMessage
            ),
          },
        );


        if (!response.ok) {

          const errorText =
            await response.text();

          console.error(
            "FCM send failed:",
            reminder.id,
            errorText,
          );

          const {
            error: failureUpdateError,
          } = await supabase
            .from("cloud_reminders")
            .update({
              status: "failed",
              updated_at:
                new Date().toISOString(),
            })
            .eq("id", reminder.id);

          if (failureUpdateError) {
            console.error(
              "Failed to record FCM failure:",
              reminder.id,
              failureUpdateError,
            );
          }

          failedCount += 1;
          continue;
        }


        // ---------------------------------
        // Mark Reminder Sent
        // ---------------------------------

        const sentAt =
          new Date().toISOString();

        const {
          error: updateError,
        } = await supabase
          .from("cloud_reminders")
          .update({
            status: "sent",
            sent_at: sentAt,
            updated_at: sentAt,
          })
          .eq("id", reminder.id);

        if (updateError) {
          throw updateError;
        }

        console.log(
          "Reminder sent:",
          reminder.id
        );

        sentCount += 1;

      } catch (error) {

        console.error(
          "Reminder processing error:",
          reminder.id,
          error,
        );

        failedCount += 1;
      }
    }


    return Response.json({
      ok: true,
      checkedAt: now,
      due: reminders.length,
      sent: sentCount,
      failed: failedCount,
    });


  } catch (error) {

    console.error(
      "send-due-reminders error:",
      error
    );

    return Response.json(
      {
        ok: false,
        error:
          error instanceof Error
            ? error.message
            : String(error),
      },
      { status: 500 },
    );
  }
});
