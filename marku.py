# -*- coding: utf-8 -*-
"""
Enhanced visual version of your SeleniumBase script.
- Adds colorful, timestamped logging and dividers for clarity.
- Wraps sleeps with a randomized helper:
    * If base_sleep < 10  -> random 1–10 seconds
    * If base_sleep >= 10 -> random 10–60 seconds
- Keeps your original flow and actions intact.
"""

from seleniumbase import SB
import time
import random
import sys
import os
from dataclasses import dataclass
from typing import Optional

# ---------- Visual styling (ANSI colors) ----------
class Style:
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    # Foreground
    FG_BLUE = "\033[34m"
    FG_CYAN = "\033[36m"
    FG_GREEN = "\033[32m"
    FG_YELLOW = "\033[33m"
    FG_MAGENTA = "\033[35m"
    FG_RED = "\033[31m"
    FG_WHITE = "\033[37m"
    # Background (lightly used)
    BG_DARK = "\033[48;5;236m"
    BG_NONE = "\033[49m"

def now_ts() -> str:
    return time.strftime("%H:%M:%S")

class VLog:
    """Simple visual logger with consistent formatting."""
    def divider(self, label: Optional[str] = None) -> None:
        bar = f"{Style.DIM}{'─'*14}{Style.RESET}"
        core = f"{Style.FG_MAGENTA}{Style.BOLD}◆{Style.RESET}"
        if label:
            print(f"\n{bar} {core} {Style.FG_MAGENTA}{label}{Style.RESET} {core} {bar}")
        else:
            print(f"\n{bar} {core}{bar}")

    def banner(self, title: str) -> None:
        line = "═" * (len(title) + 8)
        print(
            f"\n{Style.FG_CYAN}{Style.BOLD}╔{line}╗{Style.RESET}\n"
            f"{Style.FG_CYAN}{Style.BOLD}║   {title}   ║{Style.RESET}\n"
            f"{Style.FG_CYAN}{Style.BOLD}╚{line}╝{Style.RESET}"
        )

    def info(self, msg: str) -> None:
        print(f"{Style.FG_BLUE}[{now_ts()}] ℹ {Style.RESET}{msg}")

    def action(self, msg: str) -> None:
        print(f"{Style.FG_YELLOW}[{now_ts()}] ► {Style.RESET}{msg}")

    def ok(self, msg: str) -> None:
        print(f"{Style.FG_GREEN}[{now_ts()}] ✓ {Style.RESET}{msg}")

    def warn(self, msg: str) -> None:
        print(f"{Style.FG_YELLOW}[{now_ts()}] ⚠ {Style.RESET}{msg}")

    def err(self, msg: str) -> None:
        print(f"{Style.FG_RED}[{now_ts()}] ✖ {Style.RESET}{msg}")

# ---------- Config ----------
@dataclass
class Targets:
    kick_url: str = "https://kick.com/brutalles"
    twitch_url: str = "https://www.twitch.tv/brutalles"
    cookie_btn: str = 'button:contains("Accept")'
    channel_player: str = "#injected-channel-player"

vlog = VLog()
T = Targets()

# ---------- Sleep helper ----------
def randomized_sleep(base_seconds: int, sb_driver, context: str = "") -> None:
    """
    If base_seconds < 10 -> sleep random between 1 and 10
    If base_seconds >= 10 -> sleep random between 10 and 60
    """
    if base_seconds < 10:
        wait = random.randint(1, 10)
    else:
        wait = random.randint(10, 60)
    if context:
        vlog.info(f"{context}: sleeping {wait} seconds (base={base_seconds})")
    else:
        vlog.info(f"Sleeping {wait} seconds (base={base_seconds})")
    sb_driver.sleep(wait)

# ---------- Common actions ----------
def accept_cookies_if_present(sb_driver) -> None:
    if sb_driver.is_element_present(T.cookie_btn):
        vlog.action('Clicking "Accept" (cookies).')
        sb_driver.uc_click(T.cookie_btn, reconnect_time=4)
        vlog.ok("Cookies accepted.")

def solve_captcha_if_any(sb_driver) -> None:
    vlog.action("Attempting CAPTCHA interaction (if present).")
    sb_driver.uc_gui_click_captcha()
    sb_driver.uc_gui_handle_captcha()
    vlog.ok("CAPTCHA step handled (or not required).")

def visit_with_secondary(sb_driver, url: str, after_open_sleep_base: int = 10) -> None:
    """
    Opens the same URL in a secondary undetectable driver to mirror the original behavior.
    """
    vlog.divider("Secondary window")
    try:
        sec = sb_driver.get_new_driver(undetectable=True)
        vlog.action(f"Secondary open: {url}")
        sec.uc_open_with_reconnect(url, 5)
        solve_captcha_if_any(sec)
        randomized_sleep(after_open_sleep_base, sb_driver, context="Secondary post-open")
        accept_cookies_if_present(sec)
        vlog.ok("Secondary window complete.")
    except Exception as e:
        vlog.err(f"Secondary flow error: {e}")
    finally:
        # Ensure we close the extra driver to keep things tidy
        sb_driver.quit_extra_driver()
        vlog.info("Secondary window closed.")

# ---------- Main script ----------
if __name__ == "__main__":
    vlog.banner("Streamer Auto-Visit (Visual Mode)")
    vlog.info(f"Python {sys.version.split()[0]} | PID {os.getpid()}")
    vlog.divider("Session start")

    with SB(uc=True, test=True) as marku:
        # ---- KICK ----
        vlog.divider("Kick")
        vlog.action(f"Opening: {T.kick_url}")
        marku.uc_open_with_reconnect(T.kick_url, 4)
        randomized_sleep(4, marku, context="Post-open (Kick)")
        solve_captcha_if_any(marku)
        randomized_sleep(4, marku, context="Post-captcha (Kick)")
        accept_cookies_if_present(marku)

        if marku.is_element_visible(T.channel_player):
            vlog.info("Channel player detected on Kick.")
            visit_with_secondary(marku, T.kick_url, after_open_sleep_base=10)
        else:
            vlog.warn("Channel player not visible on Kick; skipping secondary.")

        randomized_sleep(1, marku, context="Between platforms")

        # ---- TWITCH ----
        vlog.divider("Twitch")
        vlog.action(f"Opening: {T.twitch_url}")
        marku.uc_open_with_reconnect(T.twitch_url, 5)
        accept_cookies_if_present(marku)

        # Mirror your original logic: always use secondary for Twitch section
        visit_with_secondary(marku, T.twitch_url, after_open_sleep_base=10)

        randomized_sleep(1, marku, context="Wrap-up")
        vlog.divider("Session end")
        vlog.ok("All tasks complete.")
