#!/usr/bin/env bash
# Builds dist/typestriker_v<version>_<arch>.deb
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
VENV="$ROOT/build/venv-linux"

[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install --quiet -r requirements-build.txt

VERSION="$("$VENV/bin/python" -c 'import typestriker; print(typestriker.__version__)')"
ARCH="$(dpkg --print-architecture)"
PACKAGE="typestriker_v${VERSION}_${ARCH}"
STAGE="$ROOT/build/deb/$PACKAGE"

"$VENV/bin/python" -m PyInstaller --noconfirm --clean --log-level WARN \
  --distpath build/pyi-linux/dist --workpath build/pyi-linux/work packaging/typestriker.spec

rm -rf "$STAGE"
mkdir -p "$STAGE/DEBIAN" "$STAGE/opt" "$STAGE/usr/bin" "$STAGE/usr/share/applications" \
         "$STAGE/usr/share/doc/typestriker" "$STAGE/usr/share/pixmaps"
cp -a build/pyi-linux/dist/typestriker "$STAGE/opt/typestriker"
find "$STAGE/opt/typestriker" -type d -exec chmod 755 {} +
find "$STAGE/opt/typestriker" -type f -exec chmod 644 {} +
find "$STAGE/opt/typestriker" -type f \( -name '*.so*' -o -name 'typestriker' \) -exec chmod 755 {} +

printf '#!/bin/sh\nexec /opt/typestriker/typestriker "$@"\n' > "$STAGE/usr/bin/typestriker"
chmod 755 "$STAGE/usr/bin/typestriker"
install -m 644 packaging/typestriker.desktop "$STAGE/usr/share/applications/typestriker.desktop"
install -m 644 assets/icon.png "$STAGE/usr/share/pixmaps/typestriker.png"
install -m 644 README.md BUGREPORT.md "$STAGE/usr/share/doc/typestriker/"
install -m 644 LICENSE "$STAGE/usr/share/doc/typestriker/copyright"

# The standard icon sizes, scaled from the master
SDL_VIDEODRIVER=dummy PYGAME_HIDE_SUPPORT_PROMPT=1 "$VENV/bin/python" - "$STAGE" <<'PY'
import os, sys
import pygame
stage = sys.argv[1]
master = pygame.image.load("assets/icon.png")
for size in (16, 24, 32, 48, 64, 128, 256, 512):
    folder = f"{stage}/usr/share/icons/hicolor/{size}x{size}/apps"
    os.makedirs(folder, exist_ok=True)
    pygame.image.save(pygame.transform.smoothscale(master, (size, size)), f"{folder}/typestriker.png")
PY

SIZE="$(du -sk "$STAGE" | cut -f1)"
cat > "$STAGE/DEBIAN/control" <<CONTROL
Package: typestriker
Version: $VERSION
Section: games
Priority: optional
Architecture: $ARCH
Depends: libc6 (>= 2.36)
Recommends: libgl1, libasound2
Installed-Size: $SIZE
Maintainer: Shouku Games <info@shoukugames.org>
Homepage: https://shoukugames.org/
Description: Typing vertical shooter for all ages
 Your ship rides on rails, so all you do is type. Press the letter or spell
 the word behind each enemy to shoot it down. Ten distinct levels in space and
 on planets, ten bosses, a Top 10 table and saved speed and accuracy per level.
CONTROL
cat > "$STAGE/DEBIAN/postinst" <<'SCRIPT'
#!/bin/sh
set -e
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -f /usr/share/icons/hicolor || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
SCRIPT
cp "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/postrm"
chmod 755 "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/postrm"

mkdir -p dist
dpkg-deb --root-owner-group -Zxz --build "$STAGE" "dist/$PACKAGE.deb" >/dev/null

# Prove the packaged game really runs: unpack it and play a few seconds
CHECK="$ROOT/build/deb/check"
rm -rf "$CHECK"
dpkg-deb -x "dist/$PACKAGE.deb" "$CHECK"
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy TYPESTRIKER_DATA="$CHECK/data" \
  "$CHECK/opt/typestriker/typestriker" --smoke-test "$CHECK/smoke.txt"
echo "Smoke test: $(cat "$CHECK/smoke.txt")"
echo "Built dist/$PACKAGE.deb ($(du -h "dist/$PACKAGE.deb" | cut -f1))"
