# Agent Guide for opengram

opengram is an unofficial, lighter fork of Telegram Desktop. This file describes
repository-wide rules for coding agents working on it.

## What this repository is

- Base: Telegram Desktop, kept in sync with upstream where possible.
- The point is to remove excess, not to add features. Prefer deleting code and
  settings over introducing new ones.
- The application calls itself **opengram**. It is not an official Telegram
  client and must never claim to be one.

## Boundaries

- Do not rewrite the per-file licence header that points at
  `telegramdesktop/tdesktop/blob/master/LEGAL`. It stays in every file.
- Do not rename identifiers, formats or wire-level constants: `.tdesktop-theme`,
  `Telegram.rcc`, `TelegramBeta_`, `TelegramDesktop.WalletVault.`,
  `window.TelegramWebProxy` and `TelegramWebviewProxy`, the `Telegram/`
  directory, the CMake target and `out/Telegram.slnx`.
- Keep the GPLv3 and OpenSSL exception notices in `LEGAL` and `LICENSE` intact.
- In user-visible text, "Telegram" stays where it means the service: Telegram
  Premium, Telegram Passport, the Telegram cloud, mobile Telegram apps. Only
  this application's own name becomes opengram.

## Building

- Windows: `docs/building-win.md`
- macOS: `docs/building-mac.md`
- GNU/Linux with Docker: `docs/building-linux.md`

A build needs your own `api_id` and `api_hash`; it fails without them.

## Commits

- Write commit messages in English, in the imperative: `opengram: drop ...`.
- Code review style rules live in `REVIEW.md`.
