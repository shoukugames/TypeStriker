# Reporting a bug in Type Striker

Found something wrong? Please tell us. Reports from young players and their parents are very welcome.

- **Email:** info@shoukugames.org
- **GitHub:** <https://github.com/shoukugames/TypeStriker/issues>
- **Website:** <https://shoukugames.org/>

A word in the game that seems unsuitable for children counts as a bug too. Please tell us which
word it was and we'll remove it.

## If the game crashed

The game saves the details to a file named `crash.log`. Please attach it to your report.

| System | Location |
|---|---|
| Linux | `~/.local/share/typestriker/crash.log` |
| Windows | `%APPDATA%\TypeStriker\crash.log` (paste this into the File Explorer address bar) |

## Bug report form

Copy this into your email or issue and fill in what you can.

```text
Game version:      (About screen, for example v0.1.0)
Installed from:    (.deb / Windows .exe / source)
Operating system:  (for example Ubuntu 24.04, or Windows 11)
Level:             (for example Level 6, Frozen Moon, during the boss)

What happened:

What you expected to happen:

Steps to make it happen again:
1.
2.
3.

Does it happen every time?   (always / sometimes / once)

Crash log or screenshot:     (attach if you have one)
```

## Known issues

| Issue | Workaround |
|---|---|
| The `.deb` needs glibc 2.36 or newer (Debian 12, Ubuntu 23.04 or later). | On older systems, run from source (see the README). |
| The Windows `.exe` is unsigned, so SmartScreen may warn about it. | Choose **More info**, then **Run anyway**. |
| The Windows `.exe` has no console, so `--version` prints nothing. | The version is on the About screen. |
| The Windows `.exe` is built and tested under Wine, and has not yet been run on a real Windows PC. | Please report any Windows-only problem. |
| Sound and music are checked by automated tests, not yet by listening on real speakers. | Please tell us about any sound that seems wrong or too loud. |
| The Japanese text has not yet been reviewed by a native speaker. | Please tell us about any wording that seems wrong. |
| Typing with a Japanese keyboard in kana mode is handled in code but untested on a real Japanese system. | If letters don't register, switch the input mode to half-width alphanumeric. |
| A non-English keyboard layout that can't produce the letters A-Z can't play. | Switch to a Latin keyboard layout while playing. |

## Reset saved data

If a saved file is damaged the game sets it aside, renamed with `.corrupt` on the end, and starts
that file fresh. To reset by hand, delete the files in the data folder listed in the README.
