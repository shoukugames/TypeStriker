"""English and Japanese text for everything outside gameplay.

The game itself (the in-game display, level banners and typing) stays in English,
because the words being typed are English.
"""

import os
import sys

ENGLISH, JAPANESE = "en", "ja"
LANGUAGE_NAMES = {ENGLISH: "English", JAPANESE: "日本語"}

_current = ENGLISH


def get_language():
    return _current


def set_language(language):
    global _current
    _current = JAPANESE if language == JAPANESE else ENGLISH


def toggle_language():
    set_language(ENGLISH if _current == JAPANESE else JAPANESE)
    return _current


def detect_language():
    """The first-run choice: Japanese on a Japanese system, otherwise English."""
    if sys.platform == "win32":
        try:
            import ctypes
            primary = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
            return JAPANESE if primary == 0x11 else ENGLISH
        except (AttributeError, OSError):
            return ENGLISH
    for name in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(name)
        if value and value not in ("C", "POSIX"):
            return JAPANESE if value.lower().startswith("ja") else ENGLISH
    return ENGLISH


def t(key, **values):
    text = STRINGS[key][1 if _current == JAPANESE else 0]
    return text.format(**values) if values else text


def level_name(level):
    return level.name if _current == ENGLISH else LEVEL_NAMES_JA[level.number]


def challenge(level):
    if level.word_length == 1:
        return t("challenge.letters")
    return t("challenge.words", n=level.word_length)


LEVEL_NAMES_JA = {
    1: "地球の軌道", 2: "小惑星帯", 3: "緑の惑星", 4: "深紅の星雲", 5: "砂漠の惑星",
    6: "氷の衛星", 7: "イオンの嵐", 8: "溶岩の惑星", 9: "母艦の船体", 10: "ブラックホール",
}

STRINGS = {
    # Home screen
    "title": ("TYPE STRIKER", "タイプストライカー"),
    "tagline": ("Every letter is a laser. Type to survive!", "1文字が1発のレーザー！タイピングで生きのびよう！"),
    "menu.start": ("Start Game", "ゲームスタート"),
    "menu.top10": ("Top 10", "トップ10"),
    "menu.progress": ("Progress", "きろく"),
    "menu.howto": ("How to Play", "遊び方"),
    "menu.about": ("About", "クレジット"),
    "menu.options": ("Options", "オプション"),
    "menu.quit": ("Quit", "終了"),
    "hint.menu": ("Arrow keys and Enter, or use the mouse.  F3: 日本語",
                  "矢印キーとEnterキー、またはマウスで選んでね。  F3: English"),
    "hint.back": ("Press Enter to return", "Enterキーでもどる"),
    # Instructions
    "howto.title": ("HOW TO PLAY", "遊び方"),
    "howto.1": ("Your ship rides on a rail, so all you need to do is type!",
                "宇宙船はレールの上を自動で進みます。タイピングに集中しよう！"),
    "howto.2": ("Press the letter behind an enemy to fire. A correct letter scores 100.",
                "敵のうしろの文字を押すと発射！正しい文字で100点です。"),
    "howto.3": ("Levels 1-3: single letters. One hit destroys each target.",
                "レベル1〜3は1文字です。1発で倒せます。"),
    "howto.4": ("Levels 4-10: words, from 2 letters up to 8. Each letter is one hit.",
                "レベル4〜10は2〜8文字の英単語です。1文字で1発当たります。"),
    "howto.5": ("Once you start a word your ship locks on. Press Backspace to switch target.",
                "単語を打ち始めるとロックオン。Backspaceキーで目標を変えられます。"),
    "howto.dodge": ("Enemies fire back! To dodge a shot, type the letters on its red tag.",
                    "敵も撃ってきます！弾の赤い札の文字を打つと、よけられます。"),
    "howto.6": ("Every level ends with a boss that takes 10 shots: finish one letter or",
                "各レベルの最後には、10発で倒せるボスが登場！1文字か1単語を"),
    "howto.7": ("word per shot. Destroying a boss is worth a 1,000 point bonus.",
                "打ち終えるたびに1発当たります。倒すと1,000点のボーナス！"),
    "howto.8": ("You have {lives} lives and a {hp}-hit hull. Enemy fire and crashes each cost one hit.",
                "ライフは{lives}つ、船体は{hp}回まで耐えられます。敵の弾や衝突で1ダメージ。"),
    "howto.9": ("Clearing a level repairs {repair} hull points.",
                "レベルをクリアすると、船体が{repair}回復します。"),
    "howto.keys": ("Esc pauses  -  F11 full screen  -  F2 mutes sound  -  F3 language",
                   "Esc: ポーズ  -  F11: フルスクリーン  -  F2: 消音  -  F3: 言語"),
    "howto.saved1": ("Speed and accuracy are saved for every level:",
                     "速さと正確さは、レベルごとに保存されます。"),
    "howto.saved2": ("see Progress on the main menu.", "メインメニューの「きろく」で見られます。"),
    # Credits
    "about.title": ("ABOUT", "クレジット"),
    "about.game": ("Type Striker  v{version}", "タイプストライカー  v{version}"),
    "about.written_by": ("Written by", "制作"),
    "about.author": ("{author} using Claude Code", "{author}（Claude Code を使用）"),
    "about.website": ("Website", "ウェブサイト"),
    "about.email": ("Email", "メール"),
    "about.license": ("Free software under the GNU GPL v3.  A Shouku Games production.",
                      "GNU GPL v3 のフリーソフトウェアです。  Shouku Games 作品"),
    "about.hint": ("Click a link to open it.  Press Enter to return.",
                   "リンクをクリックすると開きます。  Enterキーでもどる"),
    # Top 10
    "top10.title": ("TOP 10 PILOTS", "トップ10パイロット"),
    "col.name": ("NAME", "名前"),
    "col.score": ("SCORE", "スコア"),
    "col.level": ("LEVEL", "レベル"),
    "col.wpm": ("WPM", "WPM"),
    "col.accuracy": ("ACCURACY", "正確さ"),
    "col.time": ("TIME", "タイム"),
    "col.speed": ("SPEED", "速さ"),
    "col.destroyed": ("DESTROYED", "倒した数"),
    "col.missed": ("MISSED", "のがした数"),
    "col.hits": ("HITS", "ダメージ"),
    "col.result": ("RESULT", "結果"),
    # Progress
    "progress.title": ("YOUR PROGRESS", "きみのきろく"),
    "progress.speed": ("SPEED (WPM)", "速さ (WPM)"),
    "progress.played": ("PLAYED", "回数"),
    "progress.last": ("LAST", "前回"),
    "progress.best": ("BEST", "最高"),
    "progress.trend": ("SPEED TREND", "速さの変化"),
    "progress.clears": ("CLEARS", "クリア"),
    "progress.none": ("not played yet", "まだプレイしていません"),
    "progress.hint": ("Speed is in words per minute (5 letters = 1 word).  Press Enter to return.",
                      "速さは1分間に打てる単語の数です（5文字で1単語）。  Enterキーでもどる"),
    # Options
    "options.title": ("OPTIONS", "オプション"),
    "options.sound": ("Sound volume", "効果音の音量"),
    "options.music": ("Music volume", "音楽の音量"),
    "options.fullscreen": ("Full screen", "フルスクリーン"),
    "options.language": ("Language", "言語"),
    "options.back": ("Back", "もどる"),
    "options.on": ("ON", "オン"),
    "options.off": ("OFF", "オフ"),
    "options.hint": ("Up and Down to choose, Left and Right to change.  Esc to return.",
                     "上下キーで選んで、左右キーで変更。  Escキーでもどる"),
    # After a level
    "summary.title": ("LEVEL {n} CLEAR", "レベル{n} クリア！"),
    "summary.speed": ("Speed", "速さ"),
    "summary.accuracy": ("Accuracy", "正確さ"),
    "summary.letters": ("Letters typed", "打った文字数"),
    "summary.wrong": ("Wrong keys", "まちがえたキー"),
    "summary.destroyed": ("Destroyed", "倒した数"),
    "summary.missed": ("Missed", "のがした数"),
    "summary.dodged": ("Attacks dodged", "よけた攻撃"),
    "summary.hits": ("Hits taken", "受けたダメージ"),
    "summary.level_score": ("Level score", "レベルのスコア"),
    "summary.total_score": ("Total score", "合計スコア"),
    "summary.best": ("NEW BEST!", "新記録！"),
    "summary.repair": ("Hull repaired by {repair}.  Now at {hp}/{max_hp}, with {lives} lives left.",
                       "船体が{repair}回復。  現在 {hp}/{max_hp}、ライフ残り{lives}"),
    "summary.final": ("Press Enter to see your mission stats", "Enterキーで結果を見る"),
    "summary.next": ("Next: {name} ({challenge}).  Press Enter to continue.",
                     "次は「{name}」（{challenge}）。  Enterキーで進む"),
    "challenge.letters": ("Single letters", "1文字"),
    "challenge.words": ("{n}-letter words", "{n}文字の英単語"),
    # End of the game
    "results.victory": ("MISSION COMPLETE!", "ミッションコンプリート！"),
    "results.gameover": ("GAME OVER", "ゲームオーバー"),
    "results.clear": ("CLEAR", "クリア"),
    "results.lost": ("LOST", "失敗"),
    "results.qualified": ("You made the Top 10!  Press Enter to add your name.",
                          "トップ10入り！  Enterキーで名前を登録しよう"),
    "results.continue": ("Press Enter to continue", "Enterキーで進む"),
    "name.title": ("NEW TOP 10 SCORE!", "トップ10入り！"),
    "name.points": ("{score} points", "{score} 点"),
    "name.prompt": ("Enter your name (up to {n} characters)", "名前を入力してね（{n}文字まで）"),
    "name.save": ("Press Enter to save", "Enterキーで保存"),
    # Pause menu
    "pause.title": ("PAUSED", "ポーズ"),
    "pause.resume": ("Resume", "つづける"),
    "pause.quit": ("Quit to Menu", "メニューにもどる"),
    "pause.note": ("Quitting ends this game without saving the score.",
                   "もどると、このゲームのスコアは保存されません。"),
}
