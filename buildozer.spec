[app]
title = 番茄钟
package.name = pomodoro
package.domain = com.pomodoro.app
source.dir = .
source.include_exts = py,png,jpg,wav
version = 1.0
requirements = python3,kivy==2.3.0
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,VIBRATE
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33
android.arch = arm64-v8a
android.allow_backup = True
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 0
