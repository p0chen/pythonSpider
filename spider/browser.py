# -*- coding:utf-8 -*-
# @Time      :2024/8/14 20:45
# @Author    :pochen
import os
import platform
import random
import re
import time
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, BrowserContext, Page


class BaseBrowser(ABC):
    # 调试模式
    DEBUG = False

    # 本地浏览器
    IS_LOCAL_BROWSER: bool = False
    # 默认 chrom
    BROWSER: str = 'chrome'
    # chrome 浏览器 位置
    BROWSER_PATH: str = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    # 数据保存位置
    USER_DIR: str = r'C:\Users\zengyanzhi\AppData\Local\Google\Chrome\User Data'
    # 端口
    PORT = 19789
    # 无头模式
    IS_HEADLESS: bool = True
    # 是否加载图片
    IS_LOAD_IMAGE = True

    TIME_OUT = 300000
    TIME_INTERVAL: int = random.randint(3, 8)

    @abstractmethod
    async def spider(self):
        """抽象方法"""

    @staticmethod
    async def kill_chrome():
        if platform.system() == 'Windows':
            os.popen('taskkill /F /IM chrome.exe')
        else:
           os.popen('killall chrome')
        time.sleep(1)

    @property
    def startup_parameters(self):
        return dict(
            user_data_dir=self.USER_DIR,
            executable_path=self.BROWSER_PATH,
            # 要想通过这个下载文件这个必然要开  默认是False
            accept_downloads=True,
            bypass_csp=True,
            slow_mo=10,
            args=['--disable-blink-features=AutomationControlled',f'--remote-debugging-port={self.PORT}'], # 防止被检测到 浏览器被自动化控制
            headless=self.IS_HEADLESS
        )

    async def get_browser_type(self, playwright):
        if self.BROWSER == 'firefox':
            return playwright.firefox
        elif self.BROWSER == 'Safari':
            return playwright.webkit
        else:
            return playwright.chromium

    async def open_local_browser(self):
        chrome_path = r'"C:\Program Files\Google\Chrome\Application\chrome.exe"'
        debugging_port = f"--remote-debugging-port={self.PORT}"
        command = f"{chrome_path} {debugging_port}"
        os.popen(command)
        time.sleep(2)


    async def __open_browser(self, playwright):
        browser_type = await self.get_browser_type(playwright)
        if self.DEBUG:
            await self.open_local_browser()
            self.browser = await playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{self.PORT}")
            self.context: BrowserContext = self.browser.contexts[0]
            self.page: Page =self.context.pages[0]

        elif self.IS_LOCAL_BROWSER:

            try:
                self.browser = await browser_type.launch_persistent_context(**self.startup_parameters)
            except Exception:
                await self.kill_chrome()
                await self.__open_browser(playwright)
            self.context: BrowserContext = self.browser.pages[0].context
            self.page: Page = self.context.pages[0]

        else:
            self.browser = await browser_type.launch(headless=self.IS_HEADLESS)
            self.context: BrowserContext = await self.browser.new_context()
            self.page: Page = await self.context.new_page()

        if not self.IS_LOAD_IMAGE:
            await self.page.route(re.compile(r"(\.png)|(\.jpg)|(\.jpeg)"), lambda x, y: x.abort())

        # self.api_request = self.context.request
        self.page.on("response", self.response_handler)
        self.page.on("request", self.requests_handler)
        print("已经为你准备好执行环境，开始加载页面")

    async def main(self):
        try:
            async with async_playwright() as playwright:
                await self.__open_browser(playwright)
                # 隐藏webdriver属性，防止检测出来
                js = "Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});"
                await self.page.add_init_script(js)
                await self.spider()
                await self.page.wait_for_timeout(10000)
                await self.browser.close()
            print("数据已经抓取完毕..........")
        except KeyboardInterrupt:
            print('程序被手动终止......')

    def response_handler(self, request):
        pass

    def requests_handler(self, request):
        pass
