from seleniumbase import SB
from dataclasses import dataclass
from typing import List, Optional, Dict, Union, Callable
import time
import requests
import sys
import os
import random
import subprocess
import logging
from enum import Enum
from contextlib import contextmanager
from functools import wraps

# Configuration Enums
class StreamPlatform(Enum):
    KICK = "kick"
    TWITCH = "twitch"

@dataclass
class StreamConfig:
    platform: StreamPlatform
    url: str
    reconnect_time: int
    base_sleep: int

# Custom Exceptions
class CaptchaHandlingError(Exception):
    pass

class BrowserInitializationError(Exception):
    pass

# Utility Decorators
def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

def smart_sleep(duration: int) -> None:
    """Implements intelligent sleep duration based on input time"""
    if duration < 10:
        sleep_time = random.uniform(1, 10)
    else:
        sleep_time = random.uniform(10, 60)
    time.sleep(sleep_time)

class StreamManager:
    def __init__(self):
        self.streams: Dict[str, StreamConfig] = {
            "brutalles": {
                "kick": StreamConfig(
                    platform=StreamPlatform.KICK,
                    url="https://kick.com/brutalles",
                    reconnect_time=4,
                    base_sleep=4
                ),
                "twitch": StreamConfig(
                    platform=StreamPlatform.TWITCH,
                    url="https://www.twitch.tv/brutalles",
                    reconnect_time=5,
                    base_sleep=5
                )
            }
        }

    @contextmanager
    def create_session(self, uc: bool = True, test: bool = True):
        driver = None
        try:
            driver = SB(uc=uc, test=test)
            yield driver
        finally:
            if driver:
                driver.quit()

class StreamAutomation:
    def __init__(self):
        self.manager = StreamManager()
        
    @retry_on_failure(max_attempts=3)
    def handle_platform(self, driver: SB, config: StreamConfig) -> None:
        driver.uc_open_with_reconnect(config.url, config.reconnect_time)
        smart_sleep(config.base_sleep)
        
        driver.uc_gui_click_captcha()
        smart_sleep(1)
        driver.uc_gui_handle_captcha()
        smart_sleep(config.base_sleep)
        
        if driver.is_element_present('button:contains("Accept")'):
            driver.uc_click('button:contains("Accept")', reconnect_time=config.reconnect_time)
            
        if config.platform == StreamPlatform.KICK and driver.is_element_visible('#injected-channel-player'):
            self._handle_secondary_window(driver, config)
            
        if config.platform == StreamPlatform.TWITCH:
            self._handle_secondary_window(driver, config)

    def _handle_secondary_window(self, driver: SB, config: StreamConfig) -> None:
        secondary = driver.get_new_driver(undetectable=True)
        try:
            secondary.uc_open_with_reconnect(config.url, config.reconnect_time)
            secondary.uc_gui_click_captcha()
            secondary.uc_gui_handle_captcha()
            smart_sleep(10)
            
            if secondary.is_element_present('button:contains("Accept")'):
                secondary.uc_click('button:contains("Accept")', reconnect_time=config.reconnect_time)
        finally:
            driver.quit_extra_driver()

def main():
    automation = StreamAutomation()
    
    with automation.manager.create_session() as marku:
        for platform_config in automation.manager.streams["brutalles"].values():
            try:
                automation.handle_platform(marku, platform_config)
                smart_sleep(1)
            except Exception as e:
                logging.error(f"Error handling {platform_config.platform}: {str(e)}")

if __name__ == "__main__":
    main()
