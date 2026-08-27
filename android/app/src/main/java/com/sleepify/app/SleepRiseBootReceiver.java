package com.sleepify.app;

import android.app.AlarmManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

/**
 * Restores native SleepRise alarms after lifecycle events that can remove or
 * invalidate AlarmManager registrations.
 *
 * The saved entries contain the already-computed wall-clock trigger and are
 * therefore safe to re-register after boot, app replacement, or exact-alarm
 * access being granted. Local-day recalculation remains a web-layer concern.
 */
public class SleepRiseBootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) return;
        String action = intent.getAction();
        boolean boot = Intent.ACTION_BOOT_COMPLETED.equals(action);
        boolean replaced = Intent.ACTION_MY_PACKAGE_REPLACED.equals(action);
        boolean exactPermissionChanged = Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
                && AlarmManager.ACTION_SCHEDULE_EXACT_ALARM_PERMISSION_STATE_CHANGED.equals(action);
        if (!boot && !replaced && !exactPermissionChanged) return;

        Context app = context.getApplicationContext();
        if (exactPermissionChanged) {
            AlarmManager manager = (AlarmManager) app.getSystemService(Context.ALARM_SERVICE);
            if (manager == null || !manager.canScheduleExactAlarms()) return;
        }
        try {
            SleepRiseAlarmReceiver.rescheduleSaved(app);
        } catch (RuntimeException ignored) {
            // A later app-open sync can retry without crashing the system receiver.
        }
    }
}
