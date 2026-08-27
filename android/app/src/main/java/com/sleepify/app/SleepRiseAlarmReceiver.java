package com.sleepify.app;

import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.media.AudioAttributes;
import android.media.AudioFocusRequest;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.PowerManager;
import android.provider.Settings;

import androidx.core.app.NotificationCompat;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;

/**
 * Native wake-up path used in addition to the web notification layer.
 * It keeps the selected sound playing when the WebView process is not alive.
 */
public class SleepRiseAlarmReceiver extends BroadcastReceiver {
    public static final String ACTION_FIRE = "com.sleepify.app.SLEEP_RISE_ALARM_FIRE";
    private static final String ACTION_BOOT = Intent.ACTION_BOOT_COMPLETED;
    private static final String PREFS = "sleeprise_native_alarm_v81";
    private static final String IDS = "ids";
    private static final String ACTIVE_ID = "active_id";
    private static final String CHANNEL_ID = "sleeprise_native_alarm_v90";
    private static final int NOTIFICATION_BASE = 720000;
    private static final long DELIVERY_WAKELOCK_TIMEOUT_MS = 15_000L;

    private static MediaPlayer activePlayer;
    private static AudioManager audioManager;
    private static AudioFocusRequest audioFocusRequest;
    private static PowerManager.WakeLock wakeLock;
    private static PowerManager.WakeLock deliveryWakeLock;
    private static int activeNotificationId = -1;

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) return;
        String action = intent.getAction();
        if (ACTION_BOOT.equals(action)) {
            rescheduleSaved(context.getApplicationContext());
            return;
        }
        if (!ACTION_FIRE.equals(action)) return;

        int id = intent.getIntExtra("notificationId", -1);
        String sound = intent.getStringExtra("sound");
        String alarmId = intent.getStringExtra("alarmId");
        String locale = intent.getStringExtra("locale");
        String radioUrl = intent.getStringExtra("radioUrl");
        Context app = context.getApplicationContext();
        PowerManager.WakeLock handoff = acquireDeliveryWakeLock(app);
        boolean serviceStartAccepted = false;
        try {
            SleepRiseAlarmService.start(app, id, sound, alarmId, locale, radioUrl);
            serviceStartAccepted = true;
        } catch (Exception error) {
            // Fallback for devices that reject a foreground-service start.
            emergencyFallback(app, id, sound, alarmId, locale);
        } finally {
            // On success the short lock times out automatically after the
            // receiver-to-service handoff. On failure release it immediately.
            if (!serviceStartAccepted) releaseDeliveryWakeLock(handoff);
        }
    }

    public static boolean schedule(Context context, int id, long atMillis, String sound, String alarmId, String locale) {
        return schedule(context, id, atMillis, sound, alarmId, locale, "");
    }

    public static boolean schedule(Context context, int id, long atMillis, String sound, String alarmId, String locale, String radioUrl) {
        Context app = context.getApplicationContext();
        Intent intent = new Intent(app, SleepRiseAlarmReceiver.class)
                .setAction(ACTION_FIRE)
                .putExtra("notificationId", id)
                .putExtra("sound", sound == null ? "phone_alarm" : sound)
                .putExtra("alarmId", alarmId == null ? "" : alarmId)
                .putExtra("locale", normalizeLocale(locale))
                .putExtra("radioUrl", radioUrl == null ? "" : radioUrl);
        PendingIntent pending = pendingIntent(app, id, intent);
        AlarmManager alarmManager = (AlarmManager) app.getSystemService(Context.ALARM_SERVICE);
        if (alarmManager == null) return false;
        long trigger = Math.max(atMillis, System.currentTimeMillis() + 1000L);
        SharedPreferences prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        Set<String> ids = new HashSet<>(prefs.getStringSet(IDS, new HashSet<>()));
        ids.add(String.valueOf(id));
        prefs.edit()
                .putStringSet(IDS, ids)
                .putLong("at_" + id, trigger)
                .putString("sound_" + id, sound == null ? "phone_alarm" : sound)
                .putString("alarm_" + id, alarmId == null ? "" : alarmId)
                .putString("locale_" + id, normalizeLocale(locale))
                .putString("radio_" + id, radioUrl == null ? "" : radioUrl)
                .apply();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !alarmManager.canScheduleExactAlarms()) {
            // A regular alarm-clock release must not silently downgrade to an
            // inexact alarm when the user has not granted Alarms & reminders.
            // The web layer surfaces this state and opens the special-access page.
            return false;
        }
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && alarmManager.canScheduleExactAlarms()) {
                try {
                    // AlarmClock is the OS-sanctioned exact path for alarm-clock apps and is
                    // treated as a user-visible wake-up alarm during Doze/standby.
                    PendingIntent show = showIntent(app, id, alarmId, locale);
                    AlarmManager.AlarmClockInfo alarmClock = new AlarmManager.AlarmClockInfo(trigger, show);
                    alarmManager.setAlarmClock(alarmClock, pending);
                } catch (SecurityException alarmClockDenied) {
                    // Some OEMs can reject setAlarmClock after the permission check
                    // (or the user can revoke access between the check and call).
                    // Try the other exact API, then keep a non-silent inexact fallback.
                    try {
                        alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, pending);
                    } catch (SecurityException exactDenied) {
                        alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, pending);
                    }
                }
            } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                // This path is intentionally a fallback: Android may defer it in Doze.
                alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, pending);
            } else {
                alarmManager.set(AlarmManager.RTC_WAKEUP, trigger, pending);
            }
        } catch (Exception schedulingFailure) {
            android.util.Log.e("SleepRiseAlarm", "Alarm registration failed for " + id, schedulingFailure);
            return false;
        }

        SleepRiseDirectBootReceiver.save(app, id, trigger, sound, alarmId, normalizeLocale(locale));
        return true;
    }

    public static void cancelAll(Context context) {
        Context app = context.getApplicationContext();
        SharedPreferences prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        Set<String> saved = new HashSet<>(prefs.getStringSet(IDS, new HashSet<>()));
        AlarmManager alarmManager = (AlarmManager) app.getSystemService(Context.ALARM_SERVICE);
        if (alarmManager != null) {
            for (String value : saved) {
                try {
                    int id = Integer.parseInt(value);
                    Intent intent = new Intent(app, SleepRiseAlarmReceiver.class).setAction(ACTION_FIRE);
                    PendingIntent pending = pendingIntent(app, id, intent);
                    alarmManager.cancel(pending);
                    pending.cancel();
                } catch (Exception ignored) { }
            }
        }
        // Rescheduling must not silence an alarm that is currently ringing.
        // The explicit stopAlarmSound bridge is the only path allowed to stop it.
        prefs.edit().clear().apply();
        SleepRiseDirectBootReceiver.clear(app);
    }

    /** Cancel only the normal AlarmManager entry for one alarm id. */
    static void cancelScheduledEntry(Context context, int id) {
        if (id < 0) return;
        Context app = context.getApplicationContext();
        AlarmManager manager = (AlarmManager) app.getSystemService(Context.ALARM_SERVICE);
        if (manager == null) return;
        Intent intent = new Intent(app, SleepRiseAlarmReceiver.class).setAction(ACTION_FIRE);
        PendingIntent pending = pendingIntent(app, id, intent);
        try { manager.cancel(pending); } catch (Exception ignored) { }
        try { pending.cancel(); } catch (Exception ignored) { }
    }

    private static PowerManager.WakeLock acquireDeliveryWakeLock(Context context) {
        synchronized (SleepRiseAlarmReceiver.class) {
            try {
                PowerManager manager = (PowerManager) context.getSystemService(Context.POWER_SERVICE);
                if (manager == null) return null;
                if (deliveryWakeLock != null && deliveryWakeLock.isHeld()) {
                    try { deliveryWakeLock.release(); } catch (Exception ignored) { }
                }
                deliveryWakeLock = manager.newWakeLock(
                        PowerManager.PARTIAL_WAKE_LOCK,
                        "SleepRise:AlarmDelivery");
                deliveryWakeLock.setReferenceCounted(false);
                deliveryWakeLock.acquire(DELIVERY_WAKELOCK_TIMEOUT_MS);
                return deliveryWakeLock;
            } catch (Exception ignored) {
                deliveryWakeLock = null;
                return null;
            }
        }
    }

    private static void releaseDeliveryWakeLock(PowerManager.WakeLock lock) {
        synchronized (SleepRiseAlarmReceiver.class) {
            try { if (lock != null && lock.isHeld()) lock.release(); } catch (Exception ignored) { }
            if (deliveryWakeLock == lock) deliveryWakeLock = null;
        }
    }

    private static void acquireWakeLock(Context context) {
        try {
            PowerManager manager = (PowerManager) context.getSystemService(Context.POWER_SERVICE);
            if (manager == null) return;
            if (wakeLock == null) {
                wakeLock = manager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "SleepRise:AlarmFallback");
                wakeLock.setReferenceCounted(false);
            }
            if (!wakeLock.isHeld()) wakeLock.acquire(30 * 60 * 1000L);
        } catch (Exception ignored) { }
    }

    private static void requestAudioFocus(Context context) {
        try {
            audioManager = (AudioManager) context.getSystemService(Context.AUDIO_SERVICE);
            if (audioManager == null) return;
            AudioAttributes attributes = new AudioAttributes.Builder()
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .build();
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                audioFocusRequest = new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN)
                        .setAudioAttributes(attributes)
                        .setWillPauseWhenDucked(false)
                        .build();
                audioManager.requestAudioFocus(audioFocusRequest);
            } else {
                audioManager.requestAudioFocus(null, AudioManager.STREAM_ALARM,
                        AudioManager.AUDIOFOCUS_GAIN_TRANSIENT);
            }
        } catch (Exception ignored) { }
    }

    private static void releaseAudioFocus() {
        try {
            if (audioManager == null) return;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && audioFocusRequest != null) {
                audioManager.abandonAudioFocusRequest(audioFocusRequest);
            } else {
                audioManager.abandonAudioFocus(null);
            }
        } catch (Exception ignored) { }
        audioFocusRequest = null;
        audioManager = null;
    }

    public static void stopCurrent(Context context) {
        synchronized (SleepRiseAlarmReceiver.class) {
            if (activePlayer != null) {
                try { activePlayer.stop(); } catch (Exception ignored) { }
                try { activePlayer.release(); } catch (Exception ignored) { }
                activePlayer = null;
            }
            releaseAudioFocus();
            if (wakeLock != null) {
                try { if (wakeLock.isHeld()) wakeLock.release(); } catch (Exception ignored) { }
                wakeLock = null;
            }
            Context app = context.getApplicationContext();
            int id = activeNotificationId;
            activeNotificationId = -1;
            if (id >= 0) {
                NotificationManager manager = (NotificationManager) app.getSystemService(Context.NOTIFICATION_SERVICE);
                if (manager != null) manager.cancel(id);
            }
            app.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().remove(ACTIVE_ID).apply();
        }
    }

    /** Emergency path used when the foreground service cannot be promoted. */
    static void emergencyFallback(Context context, int id, String sound, String alarmId, String locale) {
        String requested = sound == null ? "phone_alarm" : sound;
        if (!playAlarmSound(context, requested) && !"phone_alarm".equals(requested)) {
            playAlarmSound(context, "phone_alarm");
        }
        showAlarmNotification(context, id, alarmId, locale);
    }

    private static boolean playAlarmSound(Context context, String sound) {
        synchronized (SleepRiseAlarmReceiver.class) {
            stopCurrent(context);
            acquireWakeLock(context);
            requestAudioFocus(context);
            String safe = String.valueOf(sound == null ? "phone_alarm" : sound)
                    .replace(".mp3", "")
                    .replace(".wav", "")
                    .replaceAll("[^a-zA-Z0-9_]", "_")
                    .toLowerCase();
            int resource = context.getResources().getIdentifier(safe, "raw", context.getPackageName());
            if (resource == 0) resource = context.getResources().getIdentifier("phone_alarm", "raw", context.getPackageName());
            if (resource == 0) resource = context.getResources().getIdentifier("alarm_default", "raw", context.getPackageName());
            if (resource == 0) return false;
            try {
                AudioAttributes attributes = new AudioAttributes.Builder()
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                        .setUsage(AudioAttributes.USAGE_ALARM)
                        .build();
                // The AudioAttributes overload creates an already-prepared player;
                // unlike create(context, resource) followed by setAudioAttributes,
                // the alarm usage is applied before preparation and therefore routes
                // through the device alarm stream as intended.
                MediaPlayer player = MediaPlayer.create(context, resource, attributes, 0);
                if (player == null) return false;
                player.setWakeMode(context, PowerManager.PARTIAL_WAKE_LOCK);
                player.setLooping(true);
                player.setVolume(1.0f, 1.0f);
                final String requestedSound = safe;
                player.setOnErrorListener((mp, what, extra) -> {
                    synchronized (SleepRiseAlarmReceiver.class) {
                        if (activePlayer != player) return true;
                    }
                    // Never leave the user with silence after a native player error.
                    if (!"phone_alarm".equals(requestedSound) && playAlarmSound(context, "phone_alarm")) return true;
                    if (!"alarm_default".equals(requestedSound) && playAlarmSound(context, "alarm_default")) return true;
                    stopCurrent(context);
                    return true;
                });
                player.start();
                activePlayer = player;
                return true;
            } catch (Exception ignored) {
                if (activePlayer != null) {
                    try { activePlayer.release(); } catch (Exception ignoredAgain) { }
                    activePlayer = null;
                }
                return false;
            }
        }
    }

    static void showAlarmNotification(Context context, int id, String alarmId, String locale) {
        ensureChannel(context);
        int notificationId = NOTIFICATION_BASE + Math.max(0, id);
        activeNotificationId = notificationId;
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putInt(ACTIVE_ID, notificationId).apply();

        Intent open = new Intent(context, MainActivity.class)
                .setAction(Intent.ACTION_MAIN)
                .addCategory(Intent.CATEGORY_LAUNCHER)
                .setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK)
                .putExtra("SLEEPRISE_ALARM_ID", alarmId == null ? "" : alarmId);
        int flags = PendingIntent.FLAG_UPDATE_CURRENT;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) flags |= PendingIntent.FLAG_IMMUTABLE;
        PendingIntent content = PendingIntent.getActivity(context, notificationId, open, flags);

        NotificationCompat.Builder builder = new NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(com.sleepify.app.R.mipmap.ic_launcher)
                .setContentTitle("SleepRise · " + notificationTitle(locale))
                .setContentText(notificationBody(locale))
                .setCategory(NotificationCompat.CATEGORY_ALARM)
                .setPriority(NotificationCompat.PRIORITY_MAX)
                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
                .setOngoing(true)
                .setAutoCancel(false)
                .setOnlyAlertOnce(true)
                .setContentIntent(content);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            builder.setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE);
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) builder.setFullScreenIntent(content, true);
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager != null) manager.notify(notificationId, builder.build());
    }

    private static void ensureChannel(Context context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) return;
        NotificationChannel channel = new NotificationChannel(CHANNEL_ID, "SleepRise alarmı", NotificationManager.IMPORTANCE_HIGH);
        channel.setDescription("SleepRise gerçek alarm sesi");
        channel.enableVibration(true);
        channel.setSound(null, null);
        manager.createNotificationChannel(channel);
    }

    private static PendingIntent pendingIntent(Context context, int id, Intent intent) {
        int flags = PendingIntent.FLAG_UPDATE_CURRENT;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) flags |= PendingIntent.FLAG_IMMUTABLE;
        return PendingIntent.getBroadcast(context, id, intent, flags);
    }

    private static PendingIntent showIntent(Context context, int id, String alarmId, String locale) {
        Intent show = new Intent(context, MainActivity.class)
                .setAction(Intent.ACTION_MAIN)
                .addCategory(Intent.CATEGORY_LAUNCHER)
                .setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK)
                .putExtra("SLEEPRISE_ALARM_ID", alarmId == null ? "" : alarmId)
                .putExtra("SLEEPRISE_ALARM_LOCALE", normalizeLocale(locale));
        int flags = PendingIntent.FLAG_UPDATE_CURRENT;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) flags |= PendingIntent.FLAG_IMMUTABLE;
        return PendingIntent.getActivity(context, 900000 + Math.max(0, id), show, flags);
    }

    public static void rescheduleSaved(Context context) {
        Context app = context.getApplicationContext();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            AlarmManager manager = (AlarmManager) app.getSystemService(Context.ALARM_SERVICE);
            if (manager == null || !manager.canScheduleExactAlarms()) return;
        }
        SharedPreferences prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        Set<String> saved = prefs.getStringSet(IDS, new HashSet<>());
        for (String value : new ArrayList<>(saved)) {
            try {
                int id = Integer.parseInt(value);
                long at = prefs.getLong("at_" + id, 0L);
                if (at <= System.currentTimeMillis() + 1000L) continue;
                schedule(context, id, at, prefs.getString("sound_" + id, "phone_alarm"), prefs.getString("alarm_" + id, ""), prefs.getString("locale_" + id, "en"), prefs.getString("radio_" + id, ""));
            } catch (Exception ignored) { }
        }
    }

    private static String normalizeLocale(String locale) {
        String value = locale == null ? "en" : locale.toLowerCase();
        if (value.length() > 2) value = value.substring(0, 2);
        return value;
    }

    private static String notificationTitle(String locale) {
        switch (normalizeLocale(locale)) {
            case "tr": return "Alarm";
            case "es": return "Alarma";
            case "de": return "Alarm";
            case "fr": return "Alarme";
            case "pt": return "Alarme";
            case "ar": return "منبه";
            case "zh": return "闹钟";
            case "ja": return "アラーム";
            default: return "Alarm";
        }
    }

    private static String notificationBody(String locale) {
        switch (normalizeLocale(locale)) {
            case "tr": return "Alarm çalıyor · görevi tamamla";
            case "es": return "La alarma está sonando · completa la tarea";
            case "de": return "Der Alarm klingelt · Aufgabe erledigen";
            case "fr": return "L’alarme sonne · terminez la tâche";
            case "pt": return "O alarme está tocando · conclua a tarefa";
            case "ar": return "المنبه يرن · أكمل المهمة";
            case "zh": return "闹钟正在响 · 完成任务";
            case "ja": return "アラームが鳴っています · タスクを完了してください";
            default: return "The alarm is ringing · complete the task";
        }
    }
}
