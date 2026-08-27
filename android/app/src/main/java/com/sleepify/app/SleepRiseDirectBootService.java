package com.sleepify.app;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.media.AudioAttributes;
import android.media.AudioFocusRequest;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.os.Build;
import android.os.IBinder;
import android.os.PowerManager;

import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;

/**
 * Direct Boot fallback. It deliberately does not touch the WebView or
 * credential-protected state. Its only job is to make a bundled alarm audible
 * before the first unlock after a reboot; the normal task UI takes over after
 * unlock.
 */
public class SleepRiseDirectBootService extends Service {
    public static final String ACTION_START = "com.sleepify.app.SLEEP_RISE_DIRECT_BOOT_START";
    public static final String ACTION_STOP = "com.sleepify.app.SLEEP_RISE_DIRECT_BOOT_STOP";
    private static final String PREFS = "sleeprise_native_alarm_direct_boot_service";
    private static final String CHANNEL_ID = "sleeprise_direct_boot_alarm";
    private static final int NOTIFICATION_ID = 821001;
    private static final long WAKELOCK_TIMEOUT_MS = 30 * 60 * 1000L;

    private static MediaPlayer player;
    private static AudioManager audioManager;
    private static AudioFocusRequest audioFocusRequest;
    private static PowerManager.WakeLock wakeLock;

    public static void start(Context context, int id, String sound, String alarmId, String locale) {
        Context app = context.getApplicationContext();
        Intent intent = new Intent(app, SleepRiseDirectBootService.class)
                .setAction(ACTION_START)
                .putExtra("notificationId", id)
                .putExtra("sound", sound == null ? "phone_alarm" : sound)
                .putExtra("alarmId", alarmId == null ? "" : alarmId)
                .putExtra("locale", locale == null ? "en" : locale);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) app.startForegroundService(intent);
        else app.startService(intent);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            stopPlayback();
            stopSelf();
            return START_NOT_STICKY;
        }

        SharedPreferences state = createDeviceProtectedStorageContext()
                .getSharedPreferences(PREFS, MODE_PRIVATE);
        if (intent != null && ACTION_START.equals(intent.getAction())) {
            state.edit()
                    .putBoolean("running", true)
                    .putInt("notificationId", intent.getIntExtra("notificationId", -1))
                    .putString("sound", intent.getStringExtra("sound"))
                    .putString("alarmId", intent.getStringExtra("alarmId"))
                    .putString("locale", intent.getStringExtra("locale"))
                    .apply();
            startDirectBootPlayback(
                    intent.getIntExtra("notificationId", -1),
                    intent.getStringExtra("sound"),
                    intent.getStringExtra("alarmId"),
                    intent.getStringExtra("locale"));
        } else if (intent == null && state.getBoolean("running", false)) {
            startDirectBootPlayback(
                    state.getInt("notificationId", -1),
                    state.getString("sound", "phone_alarm"),
                    state.getString("alarmId", ""),
                    state.getString("locale", "en"));
        }
        return START_STICKY;
    }

    private void startDirectBootPlayback(int id, String sound, String alarmId, String locale) {
        ensureChannel();
        startForeground(NOTIFICATION_ID, buildNotification(id, alarmId, locale));
        acquireWakeLock();
        requestAudioFocus();
        synchronized (SleepRiseDirectBootService.class) {
            releasePlayer();
            String requested = normalizeSound(sound);
            if (!playLocal(requested) && !"phone_alarm".equals(requested)) playLocal("phone_alarm");
            if (player == null) playLocal("alarm_default");
        }
    }

    private boolean playLocal(String sound) {
        int resource = getResources().getIdentifier(sound, "raw", getPackageName());
        if (resource == 0) return false;
        MediaPlayer next = null;
        try {
            AudioAttributes attributes = new AudioAttributes.Builder()
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .build();
            next = MediaPlayer.create(this, resource, attributes, 0);
            if (next == null) return false;
            next.setWakeMode(this, PowerManager.PARTIAL_WAKE_LOCK);
            next.setLooping(true);
            next.setVolume(1f, 1f);
            final MediaPlayer failed = next;
            next.setOnErrorListener((mp, what, extra) -> {
                synchronized (SleepRiseDirectBootService.class) {
                    if (player == failed) {
                        releasePlayer();
                        if (!"phone_alarm".equals(sound)) playLocal("phone_alarm");
                    }
                }
                return true;
            });
            player = next;
            next.start();
            return true;
        } catch (Exception error) {
            releaseQuietly(next);
            if (player == next) player = null;
            return false;
        }
    }

    private Notification buildNotification(int id, String alarmId, String locale) {
        Intent open = new Intent(this, MainActivity.class)
                .setAction(Intent.ACTION_MAIN)
                .addCategory(Intent.CATEGORY_LAUNCHER)
                .setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK)
                .putExtra("SLEEPRISE_ALARM_ID", alarmId == null ? "" : alarmId);
        PendingIntent content = PendingIntent.getActivity(
                this, NOTIFICATION_ID + 1, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Intent stop = new Intent(this, SleepRiseDirectBootService.class).setAction(ACTION_STOP);
        PendingIntent stopIntent = PendingIntent.getService(
                this, NOTIFICATION_ID + 2, stop,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(com.sleepify.app.R.mipmap.ic_launcher)
                .setContentTitle("SleepRise · " + notificationTitle(locale))
                .setContentText(notificationBody(locale))
                .setCategory(NotificationCompat.CATEGORY_ALARM)
                .setPriority(NotificationCompat.PRIORITY_MAX)
                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
                .setOngoing(true)
                .setAutoCancel(false)
                .setContentIntent(content)
                .addAction(com.sleepify.app.R.mipmap.ic_launcher, "Stop", stopIntent);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            builder.setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE);
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) builder.setFullScreenIntent(content, true);
        return builder.build();
    }

    private void ensureChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID, "SleepRise alarm", NotificationManager.IMPORTANCE_HIGH);
        channel.setDescription("Alarm fallback after device restart");
        channel.setSound(null, null);
        channel.enableVibration(true);
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager != null) manager.createNotificationChannel(channel);
    }

    private void acquireWakeLock() {
        try {
            PowerManager manager = getSystemService(PowerManager.class);
            if (manager == null) return;
            if (wakeLock != null && wakeLock.isHeld()) wakeLock.release();
            wakeLock = manager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "SleepRise:DirectBootAlarm");
            wakeLock.setReferenceCounted(false);
            wakeLock.acquire(WAKELOCK_TIMEOUT_MS);
        } catch (Exception ignored) { }
    }

    private void requestAudioFocus() {
        try {
            audioManager = getSystemService(AudioManager.class);
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

    private void releaseAudioFocus() {
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

    private void stopPlayback() {
        synchronized (SleepRiseDirectBootService.class) {
            releasePlayer();
            releaseAudioFocus();
            try {
                if (wakeLock != null && wakeLock.isHeld()) wakeLock.release();
            } catch (Exception ignored) { }
            wakeLock = null;
            getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();
            stopForeground(STOP_FOREGROUND_REMOVE);
        }
    }

    private static void releasePlayer() {
        releaseQuietly(player);
        player = null;
    }

    private static void releaseQuietly(MediaPlayer value) {
        if (value == null) return;
        try { value.stop(); } catch (Exception ignored) { }
        try { value.reset(); } catch (Exception ignored) { }
        try { value.release(); } catch (Exception ignored) { }
    }

    private static String normalizeSound(String sound) {
        return String.valueOf(sound == null ? "phone_alarm" : sound)
                .replace(".mp3", "")
                .replace(".wav", "")
                .replaceAll("[^a-zA-Z0-9_]", "_")
                .toLowerCase();
    }

    private static String normalizeLocale(String locale) {
        String value = locale == null ? "en" : locale.toLowerCase();
        return value.length() > 2 ? value.substring(0, 2) : value;
    }

    private static String notificationTitle(String locale) {
        switch (normalizeLocale(locale)) {
            case "tr": return "Alarm";
            case "es": return "Alarma";
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

    @Nullable
    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onDestroy() {
        stopPlayback();
        super.onDestroy();
    }
}
