[app]
title = ORBITIDE
package.name = orbitide
package.domain = com.theorbitide.orbitide
source.dir =.
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2

[app:android]
android.permissions = INTERNET
android.api = 33
android.ndk = 25c
android.build_tools_version = 36.0.0
android.sdk = 33
