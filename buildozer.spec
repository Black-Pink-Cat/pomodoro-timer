[app]
title = 番茄钟
package.name = pomodoro
package.domain = com.pomodoro.app
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav
version = 1.0
requirements = python3,kivy
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.0
fullscreen = 0
android.permissions = INTERNET,VIBRATE
android.api = 34
android.minapi = 26
android.ndk = 25b
android.sdk = 34
android.gradle_dependencies =
android.arch = arm64-v8a
android.allow_backup = True
android.logcat_filters = *:S python:D
ios.kivy_version = 2.3.0

[buildozer]
log_level = 2
warn_on_root = 0
