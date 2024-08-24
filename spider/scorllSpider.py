# -*- coding:utf-8 -*-
# @Time      :2024/8/16 9:20
# @Author    :pochen
import time

from spider.pageSpider import BasePageCrawler

class ScorllSpider(BasePageCrawler):
    """滚动点击动态加载爬虫"""

    # 加载次数
    loaders: int = 10
    # 加载按钮
    loader_more_loc: str = ''

    def __init__(self, url=None):
        super().__init__()
        if url:
            self.start_url = url

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls, *args, **kwargs)
        instance.num = 0
        return instance

    async def scroll_ele_view(self, i):
        print(f"第{i + 1}次加载更多数据")
        element = self.page.locator(self.loader_more_loc)
        await element.scroll_into_view_if_needed()
        await self.page.click(self.loader_more_loc)

    async def spider(self):
        await self.check()
        await self.page.goto(self.start_url, timeout=self.TIME_OUT, wait_until='load')
        await self.page.wait_for_load_state(state='load', timeout=self.TIME_OUT)
        await self.opened()
        await self.rollover_to_bottom()
        for i in range(self.loaders):
            await self.page.wait_for_load_state(state='load', timeout=self.TIME_OUT)
            data = await self.parser_data()
            await self.save_data(data)
            time.sleep(self.TIME_INTERVAL)
            await self.scroll_ele_view(i)

    async def parser_data(self):
        lists = await self.page.locator(self.data_list_loc).all()
        datas = lists[self.num:]
        data_content = []
        for li in datas:
            if len(self.data_extract_loc):
                items = dict()
                for key, loc in self.data_extract_loc.items():
                    value = self.extract_data(li, loc)
                    items.__setitem__(key, value)
            else:
                items = await li.inner_text()
                items = [item for item in items.split(self.split_str) if item]

            data_content.append(items)
            self.num += 1
        return data_content