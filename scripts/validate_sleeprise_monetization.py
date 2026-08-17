from pathlib import Path
import json
import plistlib
import re
import xml.etree.ElementTree as ET

root = Path('/home/ubuntu/sleepify-apk-github')
html = (root / 'www/index.html').read_text()
manifest_path = root / 'android/app/src/main/AndroidManifest.xml'
manifest = ET.parse(manifest_path).getroot()
android_ns = '{http://schemas.android.com/apk/res/android}'
permissions = {node.attrib.get(android_ns + 'name') for node in manifest.findall('uses-permission')}
app_meta = [node for node in manifest.findall('application/meta-data') if node.attrib.get(android_ns + 'name') == 'com.google.android.gms.ads.APPLICATION_ID']
plist = plistlib.load((root / 'ios/App/App/Info.plist').open('rb'))
pbx = (root / 'ios/App/App.xcodeproj/project.pbxproj').read_text()
package = json.loads((root / 'package.json').read_text())
plugins = json.loads((root / 'android/app/src/main/assets/capacitor.plugins.json').read_text())

checks = {
    'html_admob_layer_once': html.count('<script id="sleeprise-admob-v51">') == 1,
    'html_subscription_layer_once': html.count('<script id="sleeprise-subscription-v52">') == 1,
    'html_product_ids': all(x in html for x in ['com.sleepify.app.pro.monthly', 'com.sleepify.app.pro.yearly']),
    'html_admob_ids': all(x in html for x in ['ca-app-pub-7996356702191225/8863890276', 'ca-app-pub-7996356702191225/2298481923', 'ca-app-pub-7996356702191225/3360282152', 'ca-app-pub-7996356702191225/9302873978']),
    'android_billing_permission': 'com.android.vending.BILLING' in permissions,
    'android_admob_meta': len(app_meta) == 1 and app_meta[0].attrib.get(android_ns + 'value') == '@string/admob_app_id',
    'android_admob_string': 'ca-app-pub-7996356702191225~8756079069' in (root / 'android/app/src/main/res/values/strings.xml').read_text(),
    'android_native_purchases_plugin': any(p.get('pkg') == '@capgo/native-purchases' for p in plugins),
    'ios_admob_app_id': plist.get('GADApplicationIdentifier') == 'ca-app-pub-7996356702191225~9135353011',
    'ios_tracking_description': bool(plist.get('NSUserTrackingUsageDescription')),
    'ios_in_app_purchase_capability': 'com.apple.InAppPurchase' in pbx and 'enabled = 1' in pbx,
    'ios_native_purchases_pod': 'CapgoNativePurchases' in (root / 'ios/App/Podfile').read_text(),
    'native_purchases_dependency': '@capgo/native-purchases' in package.get('dependencies', {}),
    'admob_dependency': '@capacitor-community/admob' in package.get('dependencies', {}),
}
for name, ok in checks.items():
    print(f'{name}={ok}')
if not all(checks.values()):
    raise SystemExit('monetization validation failed')
print('monetization_validation=passed')
