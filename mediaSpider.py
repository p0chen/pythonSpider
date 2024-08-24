# -*- coding:utf-8 -*-
# @Time      :2024/8/16 20:34
# @Author    :pochen
import os
import re
import time
from faker import Faker
from moviepy.video.io import ffmpeg_tools
from playwright.async_api import Response
from spider.pageSpider import BasePageCrawler
import requests

fk = Faker()


class ImagesSpider(BasePageCrawler):
    """图片爬虫"""

    # 图片文件的前缀
    image_start_path: str = ""
    # 图片保存的路径
    image_save_path: str = ''

    async def create_save_dir(self):
        if self.image_save_path and not os.path.exists(self.image_save_path):
            os.makedirs(self.image_save_path)

    async def spider(self):
        await self.create_save_dir()
        await self.page.goto(self.start_url, timeout=self.TIME_OUT, wait_until='load')
        await self.page.wait_for_load_state(state='load', timeout=self.TIME_OUT)
        await self.opened()
        await self.page.wait_for_timeout(10000)
        await self.auto_next_page()

    async def auto_next_page(self):
        for i in range(self.pages - 1):
            await self.page.wait_for_load_state(state='load', timeout=self.TIME_OUT)
            await self.next_page_open()
            await self.rollover_to_bottom()
            await self.page.wait_for_timeout(self.TIME_INTERVAL)
            if self.next_page_btn_loc:
                try:
                    await self.page.click(self.next_page_btn_loc, timeout=10000)
                    await self.page.wait_for_timeout(self.TIME_INTERVAL)
                    await self.opened()
                except Exception as e:
                    print('没有下一页了.............')

    def save_images(self, url, content):
        url_path, name = os.path.split(url.split('/fhd?')[0].split('/')[-1])
        print('资源地址:', url)
        print("文件名称:", name)
        filepath = os.path.join(self.image_save_path, name)
        if not os.path.exists(filepath):
            with open(filepath, 'wb') as f:
                f.write(content)
                print(f'文件 {name} 保存成功')
        else:
            print(f'文件 {name} 已存在')

    async def response_handler(self, response: Response):
        """监听响应对象"""
        types = response.headers.get('content-type')
        url = response.url
        if '/fhd?' in url and types in ['image/jpeg', 'image/png', 'image/jpg', 'image/avif', 'image/webp']:
            body = await response.body()
            self.save_images(url, body)


class VideoSpider(BasePageCrawler):
    __historical_url: list = []
    __merge_media_names = set()

    # 下载的视频类型
    file_types: list = ['video/mp4']
    # 视频保存路径
    video_save_path: str = ''
    # 从url中提取文件名的规则
    file_name_pattern: str = '*************&&&&&&&&&&&&'
    audio_tag: str = '8888888888887*********%%%%%%%%%'
    video_tag: str = '8888888888887*********%%%%%%%%%'

    async def create_save_dir(self):
        if self.video_save_path and not os.path.exists(self.video_save_path):
            os.makedirs(self.video_save_path)

    async def spider(self):
        await self.create_save_dir()
        await self.page.goto(self.start_url, timeout=self.TIME_OUT, wait_until='load')
        await self.page.wait_for_timeout(3000)
        await self.opened()
        await self.page.wait_for_timeout(10000)

    def filter(self, response):
        if response.status == 206:
            return True

    def get_filename(self, url, types):
        """生成文件名：文件名需要时唯一的"""
        name = re.search(self.file_name_pattern, url)
        name = name.group(1) if name else str(int(time.time() * 1000))
        # 区分 音频文件还是视频文件
        if self.audio_tag in url:
            self.__merge_media_names.add(name)
            return f'{name}.audio'
        if self.video_tag in url:
            self.__merge_media_names.add(name)
            return f'{name}.video'
        img_type = types.split('/')[1]
        filename = f'{name}.{img_type}'
        return filename

    async def response_handler(self, response: Response):
        """处理响应对象"""
        url = response.url
        types = response.headers.get('content-type')
        if url in self.__historical_url:
            return
        self.__historical_url.append(url)
        if types not in self.file_types:
            return
        if self.filter(response):
            filename = self.get_filename(url, types)
            file_path = os.path.join(self.video_save_path, filename)
            if not os.path.exists(file_path):
                print('视频地址:', url)
                print('文件路径:', file_path)
                await self.download_video(url, file_path, response.request)
                if self.__merge_media_names:
                    try:
                        await self.merge_medias(self.__merge_media_names.pop())
                    except Exception as e:
                        print(e)
            else:
                print(f"视频已经存在，:{file_path}")
        else:
            print("不符合过虑规则，未进行下载地址：", url)

    async def merge_medias(self, name):
        """合并文件"""
        f1 = os.path.join(self.video_save_path, f'{name}.audio')
        f2 = os.path.join(self.video_save_path, f'{name}.video')
        if os.path.isfile(f1) and os.path.isfile(f2):
            f3 = os.path.join(self.video_save_path, f'{name}.mp4')
            ffmpeg_tools.ffmpeg_merge_video_audio(f1, f2, f3)
            os.remove(f1)
            os.remove(f2)
            print(f"将{name}.audio和{name}.video合并为视频文件{name}.mp4")

    @staticmethod
    async def download_video(url, filepath, request_info):
        """下载视频"""
        try:
            # 将视频文件下载到本地
            response = requests.get(url, stream=True, headers={'User-Agent': fk.user_agent(),'Referer': 'https://www.douyin.com/user/MS4wLjABAAAAOlZ8ngnt417GKBbFysKt2Q8ERj84-Wb9xypbB8_hmIc?vid=7369137414838684954'})
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        except Exception as e:
            print("文件下载失败..................")
            print(e)
        else:
            print(f"视频下载成功,保存路径为:{filepath}")
