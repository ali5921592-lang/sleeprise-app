package com.sleepify.app;

import android.Manifest;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
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
    private TextToSpeech sleepRiseTts;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        WebView webView = getBridge().getWebView();
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);
        sleepRiseTts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS && sleepRiseTts != null) {
                sleepRiseTts.setLanguage(Locale.forLanguageTag("tr-TR"));
            }
        });
        webView.addJavascriptInterface(new SleepRiseTtsBridge(), "SleepRiseTTS");
        webView.addJavascriptInterface(new SleepRiseBuildBridge(), "SleepRiseBuild");

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
        if (origin == null || !"https".equalsIgnoreCase(origin.getScheme())) {
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
        if (requestCode != REQUEST_MEDIA || pendingMediaRequest == null) return;
        PermissionRequest request = pendingMediaRequest;
        pendingMediaRequest = null;
        grantRequestedMedia(request);
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

    @Override
    public void onDestroy() {
        if (sleepRiseTts != null) {
            sleepRiseTts.stop();
            sleepRiseTts.shutdown();
        }
        super.onDestroy();
    }

    private boolean hasResource(PermissionRequest request, String resource) {
        for (String requested : request.getResources()) {
            if (resource.equals(requested)) return true;
        }
        return false;
    }
}
