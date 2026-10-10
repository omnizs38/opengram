# opengram

An unofficial, lighter fork of [Telegram Desktop][telegram_desktop] — a free and open-source
desktop client for [Telegram][telegram], built on the [Telegram API][telegram_api] and the
[MTProto][telegram_proto] secure protocol.

opengram is an independent project. It is **not affiliated with, endorsed by or sponsored by
Telegram**, and it is not an official Telegram client. Telegram is a trademark of its
respective owner.

## Status

Early stage: there are no builds yet. The first release is being prepared and will be published
in [Releases][releases]. opengram is currently based on Telegram Desktop 7.3.0.

## What is different from Telegram Desktop

* **Its own identity.** opengram uses a separate application id, config folder and autostart
  entry, so it can be installed and run next to Telegram Desktop without touching its profile.
* **No telemetry.** Crash reports and usage events are not sent anywhere. Auto-update is kept
  and checks this repository's releases.
* **Crash reports are yours to send.** After a crash opengram shows the log with a copy button
  and a button that opens a pre-filled [GitHub issue][issues]. Nothing is uploaded automatically.
* **A de-branded interface.** Window titles, menus, the About box and the update checker talk
  about opengram, not about the application it was forked from.
* **Less packaging.** Snap, UWP and the upstream release tooling are removed.

Planned: focus mode, split view (parallel chats in tabs) and a command palette.

## Building

opengram builds for Windows (64-bit), macOS and GNU/Linux.

* [Windows][win]
* [macOS][mac]
* [GNU/Linux using Docker][linux]

You need your own `api_id` and `api_hash` — the build fails without them. See
[obtaining API credentials][api_credentials].

## Third-party

* Qt 6 ([LGPL](http://doc.qt.io/qt-6/lgpl.html)) and Qt 5.15 ([LGPL](http://doc.qt.io/qt-5/lgpl.html)) slightly patched
* OpenSSL 3.5.9 ([Apache License 2.0](https://openssl-library.org/source/license/apache-license-2.0.txt))
* WebRTC ([New BSD License](https://github.com/desktop-app/tg_owt/blob/master/LICENSE))
* zlib ([zlib License](http://www.zlib.net/zlib_license.html))
* LZMA SDK 9.20 ([public domain](http://www.7-zip.org/sdk.html))
* liblzma ([public domain](http://tukaani.org/xz/))
* Google Breakpad ([License](https://chromium.googlesource.com/breakpad/breakpad/+/master/LICENSE))
* Google Crashpad ([Apache License 2.0](https://chromium.googlesource.com/crashpad/crashpad/+/master/LICENSE))
* GYP ([BSD License](https://github.com/bnoordhuis/gyp/blob/master/LICENSE))
* Ninja ([Apache License 2.0](https://github.com/ninja-build/ninja/blob/master/COPYING))
* OpenAL Soft ([LGPL](https://github.com/kcat/openal-soft/blob/master/COPYING))
* Opus codec ([BSD License](http://www.opus-codec.org/license/))
* FFmpeg ([LGPL](https://www.ffmpeg.org/legal.html))
* Guideline Support Library ([MIT License](https://github.com/Microsoft/GSL/blob/master/LICENSE))
* Range-v3 ([Boost License](https://github.com/ericniebler/range-v3/blob/master/LICENSE.txt))
* Open Sans font ([Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0.html))
* Vazirmatn font ([SIL Open Font License 1.1](https://github.com/rastikerdar/vazirmatn/blob/master/OFL.txt))
* Emoji alpha codes ([MIT License](https://github.com/emojione/emojione/blob/master/extras/alpha-codes/LICENSE.md))
* xxHash ([BSD License](https://github.com/Cyan4973/xxHash/blob/dev/LICENSE))
* QR Code generator ([MIT License](https://github.com/nayuki/QR-Code-generator#license))
* CMake ([New BSD License](https://github.com/Kitware/CMake/blob/master/Copyright.txt))
* Hunspell ([LGPL](https://github.com/hunspell/hunspell/blob/master/COPYING.LESSER))
* Ada ([Apache License 2.0](https://github.com/ada-url/ada/blob/main/LICENSE-APACHE))
* zxcvbn-c ([MIT License](https://github.com/tsyrogit/zxcvbn-c/blob/master/LICENSE.txt))
* FrequencyWords by Hermit Dave ([Creative Commons Attribution-ShareAlike 4.0](https://creativecommons.org/licenses/by-sa/4.0/))

## License

GNU GPLv3 with an OpenSSL exception. See [LICENSE][license] and [LEGAL][legal].

[//]: # (LINKS)
[telegram]: https://telegram.org
[telegram_desktop]: https://github.com/telegramdesktop/tdesktop
[telegram_api]: https://core.telegram.org
[telegram_proto]: https://core.telegram.org/mtproto
[api_credentials]: docs/api_credentials.md
[releases]: https://github.com/omnizs38/opengram/releases
[issues]: https://github.com/omnizs38/opengram/issues/new
[license]: LICENSE
[legal]: LEGAL
[win]: docs/building-win.md
[mac]: docs/building-mac.md
[linux]: docs/building-linux.md
