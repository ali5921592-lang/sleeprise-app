package com.sleepify.app;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.media.AudioAttributes;
import android.media.MediaPlayer;
import android.os.Build;
import android.os.IBinder;

import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;

/** Keeps the wake-up tone alive after the WebView process has been closed. */
public class SleepRiseAlarmService extends Service {
    public static final String ACTION_START = "com.sleepify.app.SLEEP_RISE_START_SOUND";
    public static final String ACTION_STOP = "com.sleepify.app.SLEEP_RISE_STOP_SOUND";
    private static final String CHANNEL_ID = "sleeprise_native_alarm_v81";
    private static final int NOTIFICATION_BASE = 720000;
    private static MediaPlayer player;
    private static int notificationId = -1;

    public static void start(Context context, int id, String sound, String alarmId) {
        Intent intent = new Intent(context.getApplicationContext(), SleepRiseAlarmService.class)
                .setAction(ACTION_START)
                .putExtra("notificationId", id)
                .putExtra("sound", sound == null ? "phone_alarm" : sound)
                .putExtra("alarmId", alarmId == null ? "" : alarmId);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.startForegroundService(intent);
        } else {
            context.startService(intent);
        }
    }

    public static void stop(Context context) {
        Context app = context.getApplicationContext();
        try { app.startService(new Intent(app, SleepRiseAlarmService.class).setAction(ACTION_STOP)); } catch (Exception ignored) { }
        try { app.stopService(new Intent(app, SleepRiseAlarmService.class)); } catch (Exception ignored) { }
        release(app);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            stopSelf();
            return START_NOT_STICKY;
        }
        if (intent != null && ACTION_START.equals(intent.getAction())) {
            int id = intent.getIntExtra("notificationId", -1);
            String sound = intent.getStringExtra("sound");
            String alarmId = intent.getStringExtra("alarmId");
            ensureChannel(this);
            notificationId = NOTIFICATION_BASE + Math.max(0, id);
            startForeground(notificationId, buildNotification(this, alarmId));
            play(this, sound);
        }
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        release(this);
        super.onDestroy();
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) { return null; }

    private static void play(Context context, String sound) {
        release(context);
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
            MediaPlayer next = MediaPlayer.create(context, resource);
            if (next == null) return;
            next.setAudioAttributes(new AudioAttributes.Builder()
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .build());
            next.setLooping(true);
            next.setVolume(1f, 1f);
            next.start();
            player = next;
        } catch (Exception ignored) { }
    }

    private static Notification buildNotification(Context context, String alarmId) {
        Intent open = new Intent(context, MainActivity.class)
                .setAction(Intent.ACTION_MAIN)
                .addCategory(Intent.CATEGORY_LAUNCHER)
                .setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK)
                .putExtra("SLEEPRISE_ALARM_ID", alarmId == null ? "" : alarmId);
        int flags = PendingIntent.FLAG_UPDATE_CURRENT;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) flags |= PendingIntent.FLAG_IMMUTABLE;
        PendingIntent pending = PendingIntent.getActivity(context, notificationId, open, flags);
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
                .setContentIntent(pending);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) builder.setFullScreenIntent(pending, true);
        return builder.build();
    }

    private static void ensureChannel(Context context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) return;
        NotificationChannel channel = new NotificationChannel(CHANNEL_ID, "SleepRise alarmı", NotificationManager.IMPORTANCE_HIGH);
        channel.setDescription("SleepRise gerçek alarm sesi");
        channel.enableVibration(true);
        // The actual tone is played by MediaPlayer with USAGE_ALARM, so the OS alarm volume is used.
        channel.setSound(null, null);
        manager.createNotificationChannel(channel);
    }

    private static void release(Context context) {
        synchronized (SleepRiseAlarmService.class) {
            if (player != null) {
                try { player.stop(); } catch (Exception ignored) { }
                try { player.release(); } catch (Exception ignored) { }
                player = null;
            }
            if (context != null && notificationId >= 0) {
                NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
                if (manager != null) manager.cancel(notificationId);
            }
            notificationId = -1;
        }
    }
}
