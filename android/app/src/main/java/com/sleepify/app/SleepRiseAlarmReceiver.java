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
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
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
    private static final String CHANNEL_ID = "sleeprise_native_alarm_v81";
    private static final int NOTIFICATION_BASE = 720000;

    private static MediaPlayer activePlayer;
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
        try {
            SleepRiseAlarmService.start(context.getApplicationContext(), id, sound, alarmId);
        } catch (Exception error) {
            // Fallback for devices that reject a foreground-service start.
            playAlarmSound(context.getApplicationContext(), sound);
            showAlarmNotification(context.getApplicationContext(), id, alarmId);
        }
    }

    public static void schedule(Context context, int id, long atMillis, String sound, String alarmId) {
        Context app = context.getApplicationContext();
        Intent intent = new Intent(app, SleepRiseAlarmReceiver.class)
                .setAction(ACTION_FIRE)
                .putExtra("notificationId", id)
                .putExtra("sound", sound == null ? "phone_alarm" : sound)
                .putExtra("alarmId", alarmId == null ? "" : alarmId);
        PendingIntent pending = pendingIntent(app, id, intent);
        AlarmManager alarmManager = (AlarmManager) app.getSystemService(Context.ALARM_SERVICE);
        if (alarmManager == null) return;
        long trigger = Math.max(atMillis, System.currentTimeMillis() + 1000L);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && alarmManager.canScheduleExactAlarms()) {
            alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, pending);
        } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, pending);
        } else {
            alarmManager.set(AlarmManager.RTC_WAKEUP, trigger, pending);
        }

        SharedPreferences prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        Set<String> ids = new HashSet<>(prefs.getStringSet(IDS, new HashSet<>()));
        ids.add(String.valueOf(id));
        prefs.edit()
                .putStringSet(IDS, ids)
                .putLong("at_" + id, trigger)
                .putString("sound_" + id, sound == null ? "phone_alarm" : sound)
                .putString("alarm_" + id, alarmId == null ? "" : alarmId)
                .apply();
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
        prefs.edit().clear().apply();
        stopCurrent(app);
    }

    public static void stopCurrent(Context context) {
        synchronized (SleepRiseAlarmReceiver.class) {
            if (activePlayer != null) {
                try { activePlayer.stop(); } catch (Exception ignored) { }
                try { activePlayer.release(); } catch (Exception ignored) { }
                activePlayer = null;
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

    private static void playAlarmSound(Context context, String sound) {
        synchronized (SleepRiseAlarmReceiver.class) {
            stopCurrent(context);
            String safe = String.valueOf(sound == null ? "phone_alarm" : sound)
                    .replace(".mp3", "")
                    .replace(".wav", "")
                    .replaceAll("[^a-zA-Z0-9_]", "_")
                    .toLowerCase();
            int resource = context.getResources().getIdentifier(safe, "raw", context.getPackageName());
            if (resource == 0) resource = context.getResources().getIdentifier("phone_alarm", "raw", context.getPackageName());
            if (resource == 0) resource = context.getResources().getIdentifier("alarm_default", "raw", context.getPackageName());
            if (resource == 0) return;
            try {
                MediaPlayer player = MediaPlayer.create(context, resource);
                if (player == null) return;
                AudioAttributes attributes = new AudioAttributes.Builder()
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                        .setUsage(AudioAttributes.USAGE_ALARM)
                        .build();
                player.setAudioAttributes(attributes);
                player.setLooping(true);
                player.setVolume(1.0f, 1.0f);
                player.start();
                activePlayer = player;
            } catch (Exception ignored) { }
        }
    }

    private static void showAlarmNotification(Context context, int id, String alarmId) {
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
                .setContentTitle("SleepRise")
                .setContentText("Alarm çalıyor · görevi tamamla")
                .setCategory(NotificationCompat.CATEGORY_ALARM)
                .setPriority(NotificationCompat.PRIORITY_MAX)
                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
                .setOngoing(true)
                .setAutoCancel(false)
                .setOnlyAlertOnce(true)
                .setContentIntent(content);
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

    private static void rescheduleSaved(Context context) {
        SharedPreferences prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        Set<String> saved = prefs.getStringSet(IDS, new HashSet<>());
        for (String value : new ArrayList<>(saved)) {
            try {
                int id = Integer.parseInt(value);
                long at = prefs.getLong("at_" + id, 0L);
                if (at <= System.currentTimeMillis() + 1000L) continue;
                schedule(context, id, at, prefs.getString("sound_" + id, "phone_alarm"), prefs.getString("alarm_" + id, ""));
            } catch (Exception ignored) { }
        }
    }
}
