TRUE NATIVE PACKAGES
====================

ANDROID APK
-----------
Requirements:
- Windows/Linux/macOS
- Node.js
- JDK 17+
- Android Studio + Android SDK
- Capacitor CLI

Typical flow:
npm install
npx cap add android
npx cap sync android
npx cap open android
Build the release APK from Android Studio.

WINDOWS EXE
-----------
Requirements:
- Windows 10/11
- Node.js
- Rust
- Tauri prerequisites

Typical flow:
npm install
npm run tauri build

This produces a native Windows installer.

NOTE:
The current core client is a LAN web client/PWA. Keep the server URL configurable; do not hard-code a venue's IP address.