from pathlib import Path
from PIL import Image, ImageOps

src = Path('/home/ubuntu/upload/WhatsAppImage2026-08-17at13.41.04.jpeg')
repo = Path('/home/ubuntu/sleepify-apk-github')
img = Image.open(src).convert('RGBA')
# The supplied artwork is already square; preserve the complete mark.
img = ImageOps.fit(img, (1024, 1024), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

# Web/onboarding copies.
for name, size in [('icon-192.png', 192), ('icon-512.png', 512)]:
    img.resize((size, size), Image.Resampling.LANCZOS).save(repo / 'www' / name, optimize=True)

# iOS AppIcon set currently contains a single universal 1024px slot.
ios_dir = repo / 'ios' / 'App' / 'App' / 'Assets.xcassets' / 'AppIcon.appiconset'
ios_dir.mkdir(parents=True, exist_ok=True)
img.save(ios_dir / 'AppIcon-512@2x.png', optimize=True)

# Android launcher density sizes.
sizes = {'mdpi':48, 'hdpi':72, 'xhdpi':96, 'xxhdpi':144, 'xxxhdpi':192}
for density, size in sizes.items():
    out = repo / 'android' / 'app' / 'src' / 'main' / 'res' / f'mipmap-{density}'
    out.mkdir(parents=True, exist_ok=True)
    icon = img.resize((size, size), Image.Resampling.LANCZOS)
    icon.save(out / 'ic_launcher.png', optimize=True)
    icon.save(out / 'ic_launcher_round.png', optimize=True)
    # Keep adaptive foreground consistent with the same supplied mark.
    icon.save(out / 'ic_launcher_foreground.png', optimize=True)

print('logo_source', src)
print('source_size', Image.open(src).size)
print('generated_ios', ios_dir / 'AppIcon-512@2x.png')
print('generated_android', len(sizes) * 3, 'files')
