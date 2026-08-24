package com.sleepify.app;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Receives the OS boot broadcast and restores saved SleepRise alarms. */
public class SleepRiseBootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || !Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) return;
        SleepRiseAlarmReceiver.rescheduleSaved(context.getApplicationContext());
    }
}
