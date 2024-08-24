# -*- coding:utf-8 -*-
# @Time      :2024/8/15 11:03
# @Author    :pochen
import random

from spider.browser import BaseBrowser


class BasePageCrawler(BaseBrowser):
    # 起始url
    start_url: str = ''
    # 页数
    pages: int = 1
    # 定位数据列表
    data_list_loc: str = ''
    # 提取数据
    data_extract_loc: dict = {}
    # 定位 翻页按钮位置
    next_page_btn_loc: str = ''
    # 翻页按钮高度
    next_button_distance: int = 200
    split_str: str = '\n'

    async def check(self):
        if not self.start_url:
            print("提示抓取的入口start_url没有配置")
            exit()
        if not self.data_list_loc:
            print("提示数据列表的定位器没有配置")
            exit()

    async def spider(self):
        """爬虫入口"""
        await self.check()
        await self.page.goto(self.start_url, timeout=300000, wait_until='load')
        await self.page.wait_for_load_state(state='networkidle')
        await self.opened()
        await self.auto_next_page()

    async def auto_next_page(self):
        for i in range(self.pages):
            await self.page.wait_for_load_state(state='load', timeout=self.TIME_OUT)
            await self.next_page_open()
            await self.rollover_to_bottom()
            data = await self.parser_data()
            await self.save_data(data)
            await self.page.wait_for_timeout(self.TIME_INTERVAL)
            if self.next_page_btn_loc:
                try:
                    await self.page.click(self.next_page_btn_loc, timeout=10000)
                except Exception as e:
                    print('没有下一页了.............')

    async def parser_data(self):
        """parser page data"""
        lists = await self.page.locator(self.data_list_loc).all()
        datas = []
        for li in lists:
            if len(self.data_extract_loc):
                items = dict()
                for key, loc in self.data_extract_loc.items():
                    value = await self.extract_data(li, loc)
                    items.__setitem__(key, value)
            else:
                items = await li.inner_text()
                items = [item for item in items.split(self.split_str) if item]

            datas.append(items)

        return datas

    @staticmethod
    async def extract_data(page, loc):
        """解析数据"""
        try:
            if loc[0] == 'text':
                value = await page.locator(loc[1]).inner_text()
            else:
                value = await page.locator(loc[1]).get_attribute(loc[0])
            return value
        except Exception as e:
            print("表达式：{},数据提取失败:{}".format(loc, e))
            return ''

    async def rollover_to_bottom(self):
        """慢慢的滚动到页面底部"""
        s = 0
        while True:
            height = random.randint(200, 800)
            s += height
            js = f'window.scrollBy(0,{height})'
            await self.page.evaluate(js)
            page_height = await self.page.evaluate('() => document.body.scrollHeight')
            await self.page.wait_for_timeout(random.randint(1, 3))
            if page_height - s < self.next_button_distance:
                break

    async def next_page_open(self):
        """next page open"""

    async def save_data(self, data: [dict, list, str]):
        """sava data"""
        print(data)

    async def opened(self):
        """page opened"""
        print("------page open---------")

    async def end(self):
        """spider end"""
        await self.page.close()