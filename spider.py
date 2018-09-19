import json, os
from selenium import webdriver
from selenium.common.exceptions import  NoSuchElementException
from redis import StrictRedis
import requests


# redis setting
redis_cli = StrictRedis(port=6379, host='localhost')

# base xpath or file path
chapters_xpath = '//*[@id="content"]/li/a'
img_xpaht = '//*[@id="mhpic"]'
not_found_xpath = '/html/body/pre'
save_path = '/Users/HeBee/Downloads/'


def get_fzdm_img(url, chapter_name, comic_name, error_url_list=[]):
    """get fzdm's img"""

    browser = webdriver.Chrome()
    chapter_url = url
    comic_save_path = os.path.join(save_path, comic_name)
    n = 0
    while True:
        browser.get(url)
        # 获取图片
        try:
            img = browser.find_element_by_xpath(img_xpaht)
        except NoSuchElementException as e:
            img = None
            # 如果未找到图片
            try:
                not_found = browser.find_element_by_xpath(not_found_xpath)
            except NoSuchElementException as e:
                not_found = None
            if not_found:
                print("url %s 404 该话下载结束: " % url)
                break
            else:
                print("url %s 错误: ", url)
                comic_dict_str = redis_cli.hget("spider", comic_name)
                # redis中获取 error_url_list 如果不存则创建
                if comic_dict_str:
                    error_url_list = json.dumps(
                            comic_dict_str).setdefault('error_url', [])
                else:
                    error_url_list = [chapter_url]
                    comic_dict = {'error_url', error_url_list}
                    redis_cli.hget(
                            'spider', comic_name, json.dumps(comic_dict))
        img_response = requests.get(img.get_attribute('src'))
        # 如果图片获取成功
        if img_response.status_code == 200:
            chapter_path = os.path.join(comic_save_path, chapter_name)
            if not os.path.exists(chapter_path):
                os.makedirs(chapter_path)
            with open(os.path.join(chapter_path, '%s.jpg' % n)) as f:
                f.write(img_response.content)
            print('file: %s download findished' % chapter_url)
            n += 1
            chapter_url = url + 'index_%s.html' % n


def get_comic_chapter_links():
    """通过漫画目录 获取全部 章节链接 并保存如redis"""
