package com.sleepify.app;

import android.Manifest;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.PermissionRequest;
import android.webkit.WebView;

import androidx.annotation.NonNull;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.getcapacitor.BridgeActivity;
import com.getcapacitor.BridgeWebChromeClient;

import java.util.ArrayList;
import java.util.List;

/**
 * Sleepify native permission bridge.
 *
 * The browser setting alone is insufficient in an Android WebView. This class
 * asks Android for CAMERA / RECORD_AUDIO and then explicitly grants only the
 * matching WebView resources requested by the bundled Sleepify page.
 */
public class MainActivity extends BridgeActivity {
    private static final int REQUEST_MEDIA = 4107;
    private PermissionRequest pendingMediaRequest;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        WebView webView = getBridge().getWebView();
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);

        // Keep Capacitor's native browser behaviors (dialogs, file chooser, etc.)
        // and replace only the media-permission decision with Sleepify's allowlist.
        webView.setWebChromeClient(new BridgeWebChromeClient(getBridge()) {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                runOnUiThread(() -> handleWebMediaRequest(request));
            }

            @Override
            public void onPermissionRequestCanceled(PermissionRequest request) {
                if (pendingMediaRequest == request) {
                    pendingMediaRequest = null;
                }
                super.onPermissionRequestCanceled(request);
            }
        });
    }

    private void handleWebMediaRequest(PermissionRequest request) {
        Uri origin = request.getOrigin();
        // Sleepify is bundled by Capacitor from an HTTPS-style local origin.
        // Do not grant media permissions to non-HTTPS remote or file origins.
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

        if (pendingMediaRequest != null) {
            pendingMediaRequest.deny();
        }
        pendingMediaRequest = request;
        ActivityCompat.requestPermissions(this, required.toArray(new String[0]), REQUEST_MEDIA);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != REQUEST_MEDIA || pendingMediaRequest == null) {
            return;
        }

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

        if (granted.isEmpty()) {
            request.deny();
        } else {
            request.grant(granted.toArray(new String[0]));
        }
    }

    private boolean hasResource(PermissionRequest request, String resource) {
        for (String requested : request.getResources()) {
            if (resource.equals(requested)) {
                return true;
            }
        }
        return false;
    }
}
