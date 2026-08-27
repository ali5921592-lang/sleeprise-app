package com.sleepify.app;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.util.Log;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;

/**
 * Minimal pre-unlock alarm path. It only uses device-protected state and a
 * bundled local sound; the normal WebView task UI is intentionally deferred
 * until the user unlocks the device.
 */
public class SleepRiseDirectBootReceiver extends BroadcastReceiver {
    public static final String ACTION_FIRE = "com.sleepify.app.SLEEP_RISE_DIRECT_BOOT_FIRE";
    private static final String TAG = "SleepRiseDirectBoot";
    private static final String PREFS = "sleeprise_native_alarm_direct_boot";
    private static final String IDS = "ids";
    private static final int REQUEST_BASE = 820000;

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) return;
        if (Intent.ACTION_LOCKED_BOOT_COMPLETED.equals(intent.getAction())) {
            reschedule(context.getApplicationContext());
            return;
        }
        if (!ACTION_FIRE.equals(intent.getAction())) return;

        Context app = context.getApplicationContext();
        int id = intent.getIntExtra("notificationId", -1);
        // Prevent the post-unlock/full app entry from firing the same occurrence
        // after this pre-unlock fallback has already taken ownership.
        SleepRiseAlarmReceiver.cancelScheduledEntry(app, id);
        try {
            SleepRiseDirectBootService.start(
                    app,
                    id,
                    intent.getStringExtra("sound"),
                    intent.getStringExtra("alarmId"),
                    intent.getStringExtra("locale"));
        } catch (Exception error) {
            Log.e(TAG, "Failed to start direct-boot alarm service", error);
        }
    }

    static void reschedule(Context context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return;
        Context device = context.createDeviceProtectedStorageContext();
        AlarmManager manager = (AlarmManager) device.getSystemService(Context.ALARM_SERVICE);
        if (manager == null) return;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !manager.canScheduleExactAlarms()) return;

        SharedPreferences prefs = device.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        Set<String> saved = prefs.getStringSet(IDS, new HashSet<>());
        long now = System.currentTimeMillis();
        for (String value : new ArrayList<>(saved)) {
            try {
                int id = Integer.parseInt(value);
                long at = prefs.getLong("at_" + id, 0L);
                if (at <= now + 1000L) continue;
                String sound = prefs.getString("sound_" + id, "phone_alarm");
                String alarmId = prefs.getString("alarm_" + id, "");
                String locale = prefs.getString("locale_" + id, "en");
                PendingIntent pending = pendingIntent(device, id, sound, alarmId, locale);
                manager.setAlarmClock(new AlarmManager.AlarmClockInfo(at, showIntent(device, id, alarmId)), pending);
            } catch (Exception error) {
                Log.w(TAG, "Direct-boot alarm restore failed", error);
            }
        }
    }

    static void save(Context context, int id, long at, String sound, String alarmId, String locale) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return;
        try {
            Context device = context.createDeviceProtectedStorageContext();
            SharedPreferences prefs = device.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
            Set<String> ids = new HashSet<>(prefs.getStringSet(IDS, new HashSet<>()));
            ids.add(String.valueOf(id));
            prefs.edit()
                    .putStringSet(IDS, ids)
                    .putLong("at_" + id, at)
                    .putString("sound_" + id, sound == null ? "phone_alarm" : sound)
                    .putString("alarm_" + id, alarmId == null ? "" : alarmId)
                    .putString("locale_" + id, locale == null ? "en" : locale)
                    .apply();
        } catch (Exception error) {
            Log.w(TAG, "Direct-boot alarm save failed", error);
        }
    }

    static void clear(Context context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return;
        try {
            Context device = context.createDeviceProtectedStorageContext();
            SharedPreferences prefs = device.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
            Set<String> saved = new HashSet<>(prefs.getStringSet(IDS, new HashSet<>()));
            AlarmManager manager = (AlarmManager) device.getSystemService(Context.ALARM_SERVICE);
            if (manager != null) {
                for (String value : saved) {
                    try {
                        int id = Integer.parseInt(value);
                        PendingIntent pending = pendingIntent(device, id, "", "", "en");
                        manager.cancel(pending);
                        pending.cancel();
                    } catch (Exception ignored) { }
                }
            }
            prefs.edit().clear().apply();
        } catch (Exception error) {
            Log.w(TAG, "Direct-boot alarm clear failed", error);
        }
    }

    private static PendingIntent pendingIntent(Context context, int id, String sound, String alarmId, String locale) {
        Intent intent = new Intent(context, SleepRiseDirectBootReceiver.class)
                .setAction(ACTION_FIRE)
                .putExtra("notificationId", id)
                .putExtra("sound", sound == null ? "phone_alarm" : sound)
                .putExtra("alarmId", alarmId == null ? "" : alarmId)
                .putExtra("locale", locale == null ? "en" : locale);
        return PendingIntent.getBroadcast(
                context,
                REQUEST_BASE + Math.max(0, id),
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    private static PendingIntent showIntent(Context context, int id, String alarmId) {
        Intent show = new Intent(context, MainActivity.class)
                .setAction(Intent.ACTION_MAIN)
                .addCategory(Intent.CATEGORY_LAUNCHER)
                .setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK)
                .putExtra("SLEEPRISE_ALARM_ID", alarmId == null ? "" : alarmId);
        return PendingIntent.getActivity(
                context,
                REQUEST_BASE + 100000 + Math.max(0, id),
                show,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }
}
