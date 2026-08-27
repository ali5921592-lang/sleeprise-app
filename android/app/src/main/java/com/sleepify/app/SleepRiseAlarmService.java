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
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.PowerManager;

import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;

/** Keeps the wake-up tone alive after the WebView process has been closed. */
public class SleepRiseAlarmService extends Service {
    public static final String ACTION_START = "com.sleepify.app.SLEEP_RISE_START_SOUND";
    public static final String ACTION_STOP = "com.sleepify.app.SLEEP_RISE_STOP_SOUND";
    private static final String CHANNEL_ID = "sleeprise_native_alarm_v90";
    private static final int NOTIFICATION_BASE = 720000;
    private static final String STATE_PREFS = "sleeprise_native_alarm_service";
    private static MediaPlayer alarmPlayer;
    private static MediaPlayer radioPlayer;
    private static AudioManager audioManager;
    private static AudioFocusRequest audioFocusRequest;
    private static PowerManager.WakeLock wakeLock;
    private static int notificationId = -1;
    private static long radioAttempt = 0L;
    private static String activeFallbackSound = "phone_alarm";

    public static void start(Context context, int id, String sound, String alarmId, String locale) {
        start(context, id, sound, alarmId, locale, "");
    }

    public static void start(Context context, int id, String sound, String alarmId, String locale, String radioUrl) {
        Intent intent = new Intent(context.getApplicationContext(), SleepRiseAlarmService.class)
                .setAction(ACTION_START)
                .putExtra("notificationId", id)
                .putExtra("sound", sound == null ? "phone_alarm" : sound)
                .putExtra("alarmId", alarmId == null ? "" : alarmId)
                .putExtra("locale", normalizeLocale(locale))
                .putExtra("radioUrl", radioUrl == null ? "" : radioUrl);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.startForegroundService(intent);
        } else {
            context.startService(intent);
        }
    }

    public static void stop(Context context) {
        Context app = context.getApplicationContext();
        app.getSharedPreferences(STATE_PREFS, Context.MODE_PRIVATE).edit().clear().apply();
        try { app.startService(new Intent(app, SleepRiseAlarmService.class).setAction(ACTION_STOP)); } catch (Exception ignored) { }
        try { app.stopService(new Intent(app, SleepRiseAlarmService.class)); } catch (Exception ignored) { }
        release(app);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            getSharedPreferences(STATE_PREFS, MODE_PRIVATE).edit().clear().apply();
            stopSelf();
            return START_NOT_STICKY;
        }
        if (intent != null && ACTION_START.equals(intent.getAction())) {
            int id = intent.getIntExtra("notificationId", -1);
            String sound = intent.getStringExtra("sound");
            String alarmId = intent.getStringExtra("alarmId");
            String locale = intent.getStringExtra("locale");
            String radioUrl = intent.getStringExtra("radioUrl");
            getSharedPreferences(STATE_PREFS, MODE_PRIVATE).edit()
                    .putBoolean("running", true)
                    .putInt("notificationId", id)
                    .putString("sound", sound == null ? "phone_alarm" : sound)
                    .putString("alarmId", alarmId == null ? "" : alarmId)
                    .putString("locale", locale == null ? "en" : locale)
                    .putString("radioUrl", radioUrl == null ? "" : radioUrl)
                    .apply();
            try {
                startAlarmPlayback(id, sound, alarmId, locale, radioUrl);
            } catch (Exception startupFailure) {
                // If Android/OEM rejects foreground promotion after accepting
                // startForegroundService(), do not leave the user with silence.
                android.util.Log.e("SleepRiseAlarm", "Alarm service startup failed", startupFailure);
                SleepRiseAlarmReceiver.emergencyFallback(
                        getApplicationContext(), id, sound, alarmId, locale);
                stopSelf();
            }
        } else if (intent == null) {
            SharedPreferences state = getSharedPreferences(STATE_PREFS, MODE_PRIVATE);
            if (state.getBoolean("running", false)) {
                try {
                    startAlarmPlayback(state.getInt("notificationId", -1),
                            state.getString("sound", "phone_alarm"),
                            state.getString("alarmId", ""),
                            state.getString("locale", "en"),
                            state.getString("radioUrl", ""));
                } catch (Exception startupFailure) {
                    android.util.Log.e("SleepRiseAlarm", "Sticky alarm restart failed", startupFailure);
                    SleepRiseAlarmReceiver.emergencyFallback(
                            getApplicationContext(),
                            state.getInt("notificationId", -1),
                            state.getString("sound", "phone_alarm"),
                            state.getString("alarmId", ""),
                            state.getString("locale", "en"));
                    stopSelf();
                }
            }
        }
        return START_STICKY;
    }

    private void startAlarmPlayback(int id, String sound, String alarmId, String locale, String radioUrl) {
        ensureChannel(this);
        notificationId = NOTIFICATION_BASE + Math.max(0, id);
        startForeground(notificationId, buildNotification(this, alarmId, locale));
        acquireWakeLock(this);
        requestAudioFocus(this);

        String fallbackSound = sound == null || sound.trim().isEmpty() ? "phone_alarm" : sound;
        final long attempt;
        synchronized (SleepRiseAlarmService.class) {
            activeFallbackSound = fallbackSound;
            radioAttempt++;
            attempt = radioAttempt;
            releaseRadioPlayer();
            releaseAlarmPlayer();
        }

        // Reliability rule: a bundled alarm starts immediately. Internet radio is only
        // a best-effort foreground enhancement and can never delay or suppress this tone.
        startLocalWithFallback(this, fallbackSound);
        if (radioUrl != null && !radioUrl.trim().isEmpty()) {
            prepareRadio(this, radioUrl, fallbackSound, attempt);
        }
    }

    private static boolean startLocalWithFallback(Context context, String requestedSound) {
        if (play(context, requestedSound)) return true;
        if (!"phone_alarm".equals(normalizeSound(requestedSound)) && play(context, "phone_alarm")) return true;
        return play(context, "alarm_default");
    }

    private static void prepareRadio(Context context, String url, String fallbackSound, long attempt) {
        if (url == null || url.trim().isEmpty()) return;
        final MediaPlayer next = new MediaPlayer();
        try {
            next.setWakeMode(context, PowerManager.PARTIAL_WAKE_LOCK);
            next.setAudioAttributes(new AudioAttributes.Builder()
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .build());
            next.setLooping(true);
            next.setOnPreparedListener(mp -> {
                boolean current;
                synchronized (SleepRiseAlarmService.class) {
                    current = radioPlayer == next && radioAttempt == attempt;
                }
                if (!current) {
                    releaseQuietly(next);
                    return;
                }
                try {
                    // Keep the local tone until the stream is prepared and actually starts.
                    mp.setVolume(1f, 1f);
                    mp.start();
                    synchronized (SleepRiseAlarmService.class) {
                        if (radioPlayer == next && radioAttempt == attempt) releaseAlarmPlayer();
                    }
                } catch (Exception error) {
                    handleRadioError(context, next, attempt, fallbackSound);
                }
            });
            next.setOnErrorListener((mp, what, extra) -> {
                handleRadioError(context, next, attempt, fallbackSound);
                return true;
            });
            next.setDataSource(context, android.net.Uri.parse(url.trim()));
            synchronized (SleepRiseAlarmService.class) {
                if (radioAttempt != attempt) {
                    releaseQuietly(next);
                    return;
                }
                radioPlayer = next;
            }
            // Non-blocking: local alarm is already audible while this prepares.
            next.prepareAsync();
            new Handler(Looper.getMainLooper()).postDelayed(() -> {
                boolean timedOut = false;
                try {
                    synchronized (SleepRiseAlarmService.class) {
                        timedOut = radioPlayer == next && radioAttempt == attempt && !next.isPlaying();
                    }
                } catch (Exception ignored) { }
                if (timedOut) handleRadioError(context, next, attempt, fallbackSound);
            }, 8000L);
        } catch (Exception ignored) {
            releaseQuietly(next);
            // The bundled alarm is already running; no additional fallback is needed here.
        }
    }

    private static void handleRadioError(Context context, MediaPlayer failed, long attempt, String fallbackSound) {
        boolean owned;
        synchronized (SleepRiseAlarmService.class) {
            owned = radioPlayer == failed && radioAttempt == attempt;
            if (owned) releaseRadioPlayer();
        }
        if (!owned) return;
        synchronized (SleepRiseAlarmService.class) {
            if (alarmPlayer != null) return;
        }
        startLocalWithFallback(context, fallbackSound);
    }

    private static boolean play(Context context, String sound) {
        String safe = normalizeSound(sound);
        int resource = context.getResources().getIdentifier(safe, "raw", context.getPackageName());
        if (resource == 0) return false;
        MediaPlayer next = null;
        try {
            AudioAttributes attributes = new AudioAttributes.Builder()
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .build();
            // Use the AudioAttributes-aware factory so USAGE_ALARM is applied
            // before MediaPlayer preparation. Calling setAudioAttributes after
            // create(context, resource) is too late to guarantee alarm routing.
            next = MediaPlayer.create(context, resource, attributes, 0);
            if (next == null) return false;
            next.setWakeMode(context, PowerManager.PARTIAL_WAKE_LOCK);
            next.setLooping(true);
            next.setVolume(1f, 1f);
            final MediaPlayer failedPlayer = next;
            next.setOnErrorListener((mp, what, extra) -> {
                handleLocalError(context, failedPlayer);
                return true;
            });
            synchronized (SleepRiseAlarmService.class) {
                releaseAlarmPlayer();
                alarmPlayer = next;
            }
            next.start();
            return true;
        } catch (Exception ignored) {
            releaseQuietly(next);
            synchronized (SleepRiseAlarmService.class) {
                if (alarmPlayer == next) alarmPlayer = null;
            }
            return false;
        }
    }

    private static void handleLocalError(Context context, MediaPlayer failed) {
        boolean owned;
        String fallback;
        synchronized (SleepRiseAlarmService.class) {
            owned = alarmPlayer == failed;
            fallback = activeFallbackSound;
        }
        if (!owned) return;
        synchronized (SleepRiseAlarmService.class) {
            releaseAlarmPlayer();
        }
        if (!play(context, fallback) && !play(context, "phone_alarm")) {
            play(context, "alarm_default");
        }
    }

    private static Notification buildNotification(Context context, String alarmId, String locale) {
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
                .setContentTitle("SleepRise · " + notificationTitle(locale))
                .setContentText(notificationBody(locale))
                .setCategory(NotificationCompat.CATEGORY_ALARM)
                .setPriority(NotificationCompat.PRIORITY_MAX)
                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
                .setOngoing(true)
                .setAutoCancel(false)
                .setOnlyAlertOnce(true)
                .setContentIntent(pending);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            builder.setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE);
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) builder.setFullScreenIntent(pending, true);
        return builder.build();
    }

    private static void ensureChannel(Context context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O || context == null) return;
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) return;
        NotificationChannel channel = new NotificationChannel(CHANNEL_ID, "SleepRise Alarm", NotificationManager.IMPORTANCE_HIGH);
        channel.setDescription("SleepRise alarm sound");
        channel.enableVibration(true);
        // The actual tone is played by MediaPlayer with USAGE_ALARM, so the OS alarm volume is used.
        channel.setSound(null, null);
        manager.createNotificationChannel(channel);
    }

    private static String normalizeLocale(String locale) {
        String value = locale == null ? "en" : locale.toLowerCase();
        if (value.length() > 2) value = value.substring(0, 2);
        return value;
    }

    private static String normalizeSound(String sound) {
        return String.valueOf(sound == null ? "phone_alarm" : sound)
                .replace(".mp3", "")
                .replace(".wav", "")
                .replaceAll("[^a-zA-Z0-9_]", "_")
                .toLowerCase();
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

    private static void releaseAlarmPlayer() {
        if (alarmPlayer != null) {
            releaseQuietly(alarmPlayer);
            alarmPlayer = null;
        }
    }

    private static void releaseRadioPlayer() {
        if (radioPlayer != null) {
            releaseQuietly(radioPlayer);
            radioPlayer = null;
        }
    }

    private static void releaseQuietly(MediaPlayer mediaPlayer) {
        if (mediaPlayer == null) return;
        try { mediaPlayer.stop(); } catch (Exception ignored) { }
        try { mediaPlayer.reset(); } catch (Exception ignored) { }
        try { mediaPlayer.release(); } catch (Exception ignored) { }
    }

    private static void requestAudioFocus(Context context) {
        try {
            audioManager = (AudioManager) context.getSystemService(AUDIO_SERVICE);
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

    private static void acquireWakeLock(Context context) {
        try {
            PowerManager manager = (PowerManager) context.getSystemService(POWER_SERVICE);
            if (manager == null) return;
            if (wakeLock == null) {
                wakeLock = manager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "SleepRise:Alarm");
                wakeLock.setReferenceCounted(false);
            }
            if (!wakeLock.isHeld()) wakeLock.acquire(30 * 60 * 1000L);
        } catch (Exception ignored) { }
    }

    private static void release(Context context) {
        synchronized (SleepRiseAlarmService.class) {
            radioAttempt++;
            releaseRadioPlayer();
            releaseAlarmPlayer();
            releaseAudioFocus();
            if (wakeLock != null) {
                try { if (wakeLock.isHeld()) wakeLock.release(); } catch (Exception ignored) { }
                wakeLock = null;
            }
            if (context != null && notificationId >= 0) {
                NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
                if (manager != null) manager.cancel(notificationId);
            }
            notificationId = -1;
        }
    }

    @Override
    public void onDestroy() {
        release(this);
        super.onDestroy();
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) { return null; }
}
