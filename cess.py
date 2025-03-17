
import re
import argparse
from pathlib import Path
from browser_automation import BrowserManager

from selenium.webdriver.common.by import By

from browser_automation import Node
from utils import Utility

class Cess:
    def __init__(self, node: Node, profile: dict) -> None:
        self.driver = node._driver
        self.node = node
        self.profile_name = profile.get('profile_name')
        self.email_x = profile.get('email_x')
        self.username_x = profile.get('username_x')
        self.pass_x = profile.get('pass_x')

    def login_x(self):
        self.node.go_to(f'https://x.com/home')
        if self.node.find(By.CSS_SELECTOR, 'button[data-testid="SideNav_AccountSwitcher_Button"]'):
            self.node.log('Đã đăng nhập X')
            return True
        
        actions = [
            (self.node.go_to, 'https://x.com/i/flow/login'),
            (self.node.find_and_input, By.CSS_SELECTOR, 'input[autocomplete="username"]', self.username_x, None, 0.1),
            (self.node.find_and_click, By.XPATH, '//span[text()="Next"]'),
            (self.node.find_and_input, By.CSS_SELECTOR, 'input[name="password"]', self.pass_x, None, 0.1),
            (self.node.find_and_click, By.XPATH, '//span[text()="Log in"]'),
        ]
        if self.node.execute_chain(actions=actions, message_error='login_x thất bại'):
            return self.login_x()
        
        return False

    def connect_x(self):
        actions =[
            (self.node.go_to, 'https://cess.network/deshareairdrop/login'),
            (self.node.find_and_click, By.CSS_SELECTOR, 'img[alt="icon_checked"]'),
            (self.node.find_and_click, By.XPATH, '//p[text()="Continue with X"]'),
            (self.node.find_and_click, By.CSS_SELECTOR, 'input[id="allow"]'),
        ]

        return self.node.execute_chain(actions=actions, message_error="connect_x bị lỗi")

    def check_in(self):
        self.node.go_to('https://cess.network/deshareairdrop')
        text_button_check_in = self.node.get_text(By.XPATH, '//div[div[p[text()="Daily Check-in"]]]//button')
        if text_button_check_in == 'Check-in':
            if self.node.find_and_click(By.XPATH, '//button[text()="Check-in"]'):
                self.node.find_and_click(By.CSS_SELECTOR, 'body')
        elif ":" in text_button_check_in:
            self.node.log(f'Quay lại check - in sau: {text_button_check_in} ')
        
        text_button_retweet = self.node.get_text(By.XPATH, '//div[div[p[text()="Daily Retweet"]]]//button')
        if text_button_retweet == 'Retweet':
            self.node.find_and_click(By.XPATH, '//button[text()="Retweet"]')
            self.node.switch_tab('https://cess.network/')
            if self.node.find_and_click(By.XPATH, '//button[text()="Forwarded & Get Points"]'):
                self.node.find_and_click(By.XPATH, '//p[text()="success"]')
        elif ":" in text_button_retweet:
            self.node.log(f'Quay lại Retweet sau: {text_button_check_in} ')
        
        return True

    def _run_logic(self):
        if not self.login_x():
            self.node.snapshot(f'[cess] Login X bị lỗi')
        
        if not self.connect_x():
            self.node.snapshot(f'[cess] Connect X bị lỗi')

        self.check_in()
        
class Auto:
    def __init__(self, node: Node, profile) -> None:
        self.node = node
        self.profile = profile
        
    def _run(self):
        Cess(self.node, self.profile)._run_logic()

class Setup:
    def __init__(self, node: Node, profile) -> None:
        self.node = node
        self.profile = profile
        
    def _run(self):
        self.node.go_to('https://x.com')
        self.node.new_tab('https://cess.network/deshareairdrop/')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto', action='store_true', help="Chạy ở chế độ tự động")
    parser.add_argument('--headless', action='store_true', help="Chạy trình duyệt ẩn")
    args = parser.parse_args()

    DATA_DIR = Path(__file__).parent/'data.txt'

    if not DATA_DIR.exists():
        print(f"File {DATA_DIR} không tồn tại. Dừng mã.")
        exit()

    proxy_re = re.compile(r"^(?:\w+:\w+@)?\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}$")
    PROFILES = []
    num_parts = 4 #số dữ liệu, không bao gồm proxy

    with open(DATA_DIR, 'r') as file:
        data = file.readlines()

    for line in data:
        parts = [part.strip() for part in line.strip().split('|')]

        proxy_re = re.compile(r"^(?:\w+:\w+@)?\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}$")
        proxy_info = parts[-1] if proxy_re.match(parts[-1]) else None
        if proxy_info:
            parts = parts[:-1]
            
        if len(parts) < num_parts:
            print(f"Warning: Dữ liệu không hợp lệ - {line}")
            continue        
    
        profile_name, email_x, username_x, pass_x, *_ = (parts + [None] * num_parts)[:num_parts]

        PROFILES.append({
            'profile_name': profile_name,
            'email_x': email_x,
            'username_x': username_x,
            'pass_x': pass_x,
            'proxy_info': proxy_info
        })


    browser_manager = BrowserManager(AutoHandlerClass=Auto, SetupHandlerClass=Setup)
    # browser_manager.run_browser(PROFILES[1])
    browser_manager.run_terminal(
        profiles=PROFILES,
        max_concurrent_profiles=4,
        auto=args.auto,
        headless=args.headless
    )
