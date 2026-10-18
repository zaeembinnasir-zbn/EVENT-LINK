ANDROID APK BUILD

Use Capacitor around the client folder.
Prerequisites: Node.js, Android Studio, JDK 17+.
Typical steps:
npm install @capacitor/core @capacitor/cli
npx cap init "EventLink Local" "com.eventlink.local"
npx cap add android
npx cap copy android
npx cap open android

Set the Android app to use the local EventLink server URL discovered by the user/QR code. Do not hard-code a venue IP.
Build an APK from Android Studio.
