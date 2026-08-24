package com.sleepify.app;

import android.Manifest;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.Build;
import android.content.Intent;
import android.view.KeyEvent;
import android.speech.tts.TextToSpeech;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.WebView;

import androidx.annotation.NonNull;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.getcapacitor.BridgeActivity;
import com.getcapacitor.BridgeWebChromeClient;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * SleepRise native permission and phone TTS bridge.
 *
 * The bundled page requests camera/microphone through WebView. Android runtime
 * permission and WebView resource permission must both be granted. The TTS
 * bridge lets the breathing guide speak on Android devices where Web Speech
 * voices are not exposed by the WebView.
 */
public class MainActivity extends BridgeActivity {
    private static final int REQUEST_MEDIA = 4107;
    private PermissionRequest pendingMediaRequest;
    private boolean pendingCameraBridgeRequest = false;
    private TextToSpeech sleepRiseTts;
    private boolean alarmActive = false;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        WebView webView = getBridge().getWebView();
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);
        webView.getSettings().setMediaPlaybackRequiresUserGesture(false);
        sleepRiseTts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS && sleepRiseTts != null) {
                sleepRiseTts.setLanguage(Locale.forLanguageTag("tr-TR"));
            }
        });
        webView.addJavascriptInterface(new SleepRiseTtsBridge(), "SleepRiseTTS");
        webView.addJavascriptInterface(new SleepRiseBuildBridge(), "SleepRiseBuild");
        webView.addJavascriptInterface(new SleepRiseNativeBridge(), "SleepRiseNative");
        webView.addJavascriptInterface(new SleepRiseAlarmBridge(), "SleepRiseAlarmNative");
        webView.postDelayed(() -> dispatchNativeAlarmIntent(getIntent()), 900);

        webView.setWebChromeClient(new BridgeWebChromeClient(getBridge()) {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                runOnUiThread(() -> handleWebMediaRequest(request));
            }

            @Override
            public void onPermissionRequestCanceled(PermissionRequest request) {
                if (pendingMediaRequest == request) pendingMediaRequest = null;
                super.onPermissionRequestCanceled(request);
            }
        });
    }

    private final class SleepRiseTtsBridge {
        @JavascriptInterface
        public void speak(String text, String language, float rate) {
            runOnUiThread(() -> {
                if (sleepRiseTts == null || text == null || text.trim().isEmpty()) return;
                try {
                    Locale locale = Locale.forLanguageTag(
                            language == null ? "tr-TR" : language.replace('_', '-'));
                    sleepRiseTts.setLanguage(locale);
                    sleepRiseTts.setSpeechRate(Math.max(0.65f, Math.min(1.45f, rate)));
                    sleepRiseTts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "sleeprise-tts");
                } catch (Exception ignored) { }
            });
        }

        @JavascriptInterface
        public void stop() {
            runOnUiThread(() -> {
                if (sleepRiseTts != null) sleepRiseTts.stop();
            });
        }
    }

    private final class SleepRiseBuildBridge {
        @JavascriptInterface
        public boolean isDebug() { return (getApplicationInfo().flags & android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE) != 0; }
    }

    private void handleWebMediaRequest(PermissionRequest request) {
        Uri origin = request.getOrigin();
        if (origin == null || !isAllowedMediaOrigin(origin)) {
            request.deny();
            return;
        }

        boolean asksForAudio = hasResource(request, PermissionRequest.RESOURCE_AUDIO_CAPTURE);
        boolean asksForVideo = hasResource(request, PermissionRequest.RESOURCE_VIDEO_CAPTURE);
        if (!asksForAudio && !asksForVideo) {
            request.deny();
            return;
        }

        List<String> required = new ArrayList<>();
        if (asksForAudio && ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            required.add(Manifest.permission.RECORD_AUDIO);
        }
        if (asksForVideo && ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                != PackageManager.PERMISSION_GRANTED) {
            required.add(Manifest.permission.CAMERA);
        }

        if (required.isEmpty()) {
            grantRequestedMedia(request);
            return;
        }
        if (pendingMediaRequest != null) pendingMediaRequest.deny();
        pendingMediaRequest = request;
        ActivityCompat.requestPermissions(this, required.toArray(new String[0]), REQUEST_MEDIA);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != REQUEST_MEDIA) return;
        if (pendingMediaRequest != null) {
            PermissionRequest request = pendingMediaRequest;
            pendingMediaRequest = null;
            grantRequestedMedia(request);
            return;
        }
        if (pendingCameraBridgeRequest) {
            pendingCameraBridgeRequest = false;
            boolean granted = ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                    == PackageManager.PERMISSION_GRANTED;
            getBridge().getWebView().evaluateJavascript(
                    "window.SleepRiseCameraPermissionResult && window.SleepRiseCameraPermissionResult(" + granted + ")",
                    null);
        }
    }

    private void grantRequestedMedia(PermissionRequest request) {
        List<String> granted = new ArrayList<>();
        if (hasResource(request, PermissionRequest.RESOURCE_AUDIO_CAPTURE)
                && ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                == PackageManager.PERMISSION_GRANTED) {
            granted.add(PermissionRequest.RESOURCE_AUDIO_CAPTURE);
        }
        if (hasResource(request, PermissionRequest.RESOURCE_VIDEO_CAPTURE)
                && ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                == PackageManager.PERMISSION_GRANTED) {
            granted.add(PermissionRequest.RESOURCE_VIDEO_CAPTURE);
        }
        if (granted.isEmpty()) request.deny();
        else request.grant(granted.toArray(new String[0]));
    }

    private final class SleepRiseAlarmBridge {
        @JavascriptInterface
        public void scheduleAlarm(int id, long atMillis, String sound, String alarmId, String locale) {
            SleepRiseAlarmReceiver.schedule(MainActivity.this, id, atMillis, sound, alarmId, locale);
        }

        @JavascriptInterface
        public void cancelAll() {
            SleepRiseAlarmReceiver.cancelAll(MainActivity.this);
        }

        @JavascriptInterface
        public void stopAlarmSound() {
            SleepRiseAlarmService.stop(MainActivity.this);
            SleepRiseAlarmReceiver.stopCurrent(MainActivity.this);
        }
    }

    private final class SleepRiseNativeBridge {
        @JavascriptInterface
        public void setAlarmActive(boolean active) { alarmActive = active; }

        @JavascriptInterface
        public boolean isCameraGranted() {
            return ContextCompat.checkSelfPermission(MainActivity.this, Manifest.permission.CAMERA)
                    == PackageManager.PERMISSION_GRANTED;
        }

        @JavascriptInterface
        public boolean requestCameraPermission() {
            if (isCameraGranted()) return true;
            runOnUiThread(() -> {
                if (isCameraGranted()) {
                    getBridge().getWebView().evaluateJavascript(
                            "window.SleepRiseCameraPermissionResult && window.SleepRiseCameraPermissionResult(true)", null);
                    return;
                }
                pendingCameraBridgeRequest = true;
                ActivityCompat.requestPermissions(MainActivity.this,
                        new String[]{Manifest.permission.CAMERA}, REQUEST_MEDIA);
            });
            return false;
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        dispatchNativeAlarmIntent(intent);
    }

    private void dispatchNativeAlarmIntent(Intent intent) {
        if (intent == null) return;
        String alarmId = intent.getStringExtra("SLEEPRISE_ALARM_ID");
        if (alarmId == null || alarmId.isEmpty()) return;
        String escaped = alarmId.replace("\\", "\\\\").replace("'", "\\'");
        dispatchNativeAlarmIntent(getBridge().getWebView(), escaped, 0);
    }

    private void dispatchNativeAlarmIntent(WebView webView, String escapedAlarmId, int attempt) {
        if (webView == null || isFinishing() || (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1 && isDestroyed())) return;
        long delay = attempt == 0 ? (webView.getUrl() == null ? 700L : 120L) : 250L;
        webView.postDelayed(() -> webView.evaluateJavascript(
                "typeof window.SleepRiseNativeAlarmAction === 'function' ? String(window.SleepRiseNativeAlarmAction('" + escapedAlarmId + "')) : 'waiting'",
                result -> {
                    if (attempt < 20 && (result == null || result.contains("waiting") || result.contains("false"))) {
                        dispatchNativeAlarmIntent(webView, escapedAlarmId, attempt + 1);
                    }
                }), delay);
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_VOLUME_DOWN && alarmActive) {
            WebView webView = getBridge().getWebView();
            webView.evaluateJavascript("window.SleepRiseVolumeSnooze && window.SleepRiseVolumeSnooze()", null);
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        if (alarmActive) {
            WebView webView = getBridge().getWebView();
            webView.evaluateJavascript("window.SleepRisePolicyBlock && window.SleepRisePolicyBlock()", null);
            return;
        }
        super.onBackPressed();
    }

    @Override
    public void onDestroy() {
        if (sleepRiseTts != null) {
            sleepRiseTts.stop();
            sleepRiseTts.shutdown();
        }
        super.onDestroy();
    }

    private boolean isAllowedMediaOrigin(Uri origin) {
        if ("https".equalsIgnoreCase(origin.getScheme())) return true;
        String host = origin.getHost();
        return "http".equalsIgnoreCase(origin.getScheme())
                && ("localhost".equalsIgnoreCase(host) || "127.0.0.1".equals(host));
    }

    private boolean hasResource(PermissionRequest request, String resource) {
        for (String requested : request.getResources()) {
            if (resource.equals(requested)) return true;
        }
        return false;
    }
}
