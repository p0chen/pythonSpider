# -*- coding:utf-8 -*-
# @Time      :2024/8/16 10:43
# @Author    :pochen
import random
import time
from spider.pageSpider import BasePageCrawler


class DeepPage:
    def __init__(self, url: str, data: [dict, list], locs: dict = None, callback=None):
        self.url = url
        self.data = data
        self.locs = locs if locs else {}
        self.callback = callback


class DeepPageCrawler(BasePageCrawler):
    # 深度爬取等待时间，防止过快被封
    open_page_interval: int = 3
    # 深度url的提取规则
    deep_link_url: str = ''
    # 深度页面数据提取规则
    deep_data_extract_loc: dict = {}

    async def auto_next_page(self):
        for i in range(self.pages):
            await self.page.wait_for_load_state(state='load', timeout=self.TIME_OUT)
            await self.next_page_open()
            await self.rollover_to_bottom()
            data_content = await self.parser_data()
            for data in data_content:
                await self.deep_page_open(data)
            await self.page.wait_for_timeout(self.TIME_INTERVAL)
            if self.next_page_btn_loc:
                try:
                    await self.page.click(self.next_page_btn_loc, timeout=10000)
                except Exception as e:
                    print('没有下一页了.............')

    async def parser_data(self):
        """parser page data"""
        lists = await self.page.locator(self.data_list_loc).all()
        data_content = []
        for li in lists:
            items = dict()
            if self.data_extract_loc:
                for key, loc in self.data_extract_loc.items():
                    value = await self.extract_data(li, loc)
                    items.__setitem__(key, value)
            link_url = await li.locator(self.deep_link_url).first.evaluate('(e) => e.href')
            data_content.append(DeepPage(link_url, items))

        return data_content

    async def deep_page_open(self, item:[DeepPage, list, dict]):
        """深度页面处理"""
        if isinstance(item, DeepPage):
            time.sleep(self.open_page_interval)
            page = await self.context.new_page()
            await page.goto(item.url, timeout=self.TIME_OUT, wait_until='load')
            await page.wait_for_load_state(state='load')
            await page.evaluate(f'window.scrollBy(0,{random.randint(200, 500)})')

            if item.callback:
                result = await item.callback(page, item.data, item.locs)
            else:
                result = await self.deep_page_callback(page, item.data, item.locs)
            await page.close()
            await self.deep_page_open(result)
        else:
            await self.save_data(item)

    async def deep_page_callback(self, page, data: [dict, list], locs=None):
        """deep page parser"""
        locs = locs if locs else self.deep_data_extract_loc
        for key, loc in locs.items():
            value = await self.extract_data(page, loc)
            if isinstance(data, list):
                data.append(value)
            elif isinstance(data, dict):
                data.__setitem__(key, value)
        return data

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
