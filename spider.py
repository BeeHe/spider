import json
import os
import time
import traceback
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from redis import StrictRedis
import requests


# redis setting
redis_cli = StrictRedis(port=6379, host='localhost', db=1)

# base xpath or file path
chapters_xpath = '//*[@id="content"]/li/a'
img_xpaht = '//*[@id="mhpic"]'
not_found_xpath = '/html/body/pre'
save_path = '/Users/HeBee/Downloads/'


def get_fzdm_img(browser, url, chapter_name, comic_name, error_url_list=[]):
    """get fzdm's img"""

    is_download_success = True
    # browser = webdriver.Chrome()
    chapter_url = url
    comic_save_path = os.path.join(save_path, comic_name)
    n = 0
    while True:
        browser.get(chapter_url)
        time.sleep(3)
        # 获取图片
        is_success, img = try_get_element(browser, img_xpaht)
        # 如果 is_success 为False 表示查找失败
        if not is_success:
            is_success, not_found = try_get_element(browser, not_found_xpath)
            _, not_anymore = try_get_element(
                    browser, '//*[@id="pjax-container"]')

            if is_success:
                print("url %s 该话下载结束: 共 %s 页" % (url, n+1))
                return is_download_success
            elif '  沒有啦  ' in not_anymore.text:
                print("url %s (没有啦)该话下载结束: 共 %s 页" % (url, n+1))
                return is_download_success
            else:
                print("url %s 错误: " % url)
                comic_dict_str = redis_cli.hget("spider", comic_name)
                # redis中获取 error_url_list 如果不存则创建
                if comic_dict_str:
                    comic_dict = json.loads(comic_dict_str)
                    error_url_list = comic_dict.setdefault('error_url', [])
                    error_url_list.append(chapter_url)
                else:
                    error_url_list = [chapter_url]
                    comic_dict = {'error_url': error_url_list}
                # 保存错误信息
                redis_cli.hset('spider', comic_name, json.dumps(comic_dict))
                is_download_success = False
                return is_download_success

        img_response = requests.get(img.get_attribute('src'))
        # 如果图片获取成功
        if img_response.status_code == 200:
            chapter_path = os.path.join(comic_save_path, chapter_name)
            if not os.path.exists(chapter_path):
                os.makedirs(chapter_path)
            with open(os.path.join(chapter_path, '%s.jpg' % n), 'wb') as f:
                f.write(img_response.content)
            print('file: %s download findished' % chapter_url)
            n += 1
            chapter_url = url + 'index_%s.html' % n
        else:
            print('%s 第%s页 下载失败' %
                  (chapter_name, n), img_response.status_code)
            is_download_success = False
            n += 1
            chapter_url = url + 'index_%s.html' % n


def get_comic_chapter_links(
        browser, link, comic_name, start=None, end=None, step=None):
    """通过漫画目录 获取全部 章节链接 并保存入redis"""
    browser.get(link)
    chapters_list = \
        browser.find_elements_by_xpath(chapters_xpath)[start:end:step]
    chapter_name_list = [chapter.get_attribute('text')
                         for chapter in chapters_list]
    chapter_link_list = [chapter.get_attribute('href')
                         for chapter in chapters_list]
    # 将获取到的 link 和 name 按顺序 插入 redis中
    redis_cli.rpush('%s_chapters_link' % comic_name, *chapter_link_list)
    redis_cli.rpush('%s_chapters_name' % comic_name, *chapter_name_list)
    print("获取章节成功 共 %s 最后一章为: %s" % (
        len(chapter_name_list), chapter_name_list[0]))
    return True


def try_get_element(browser, xpath):
    """ try 获取 element """
    try:
        element = browser.find_element_by_xpath(xpath)
    except NoSuchElementException as e:
        exstr = traceback.format_exc()
        # 未找到该元素
        print('----' * 4)
        print(exstr)
        return False, None
    return True, element


def main(url, comic_name, config):
    browser = webdriver.Chrome()
    chapter_link_list = redis_cli.lrange(
            '%s_chapters_link' % comic_name, 0, -1)
    if not chapter_link_list:
        chapter_link_list = redis_cli.lrange(
                '%s_error_url' % comic_name, 0, -1)
        if chapter_link_list:
            link_list = []
            name_list = []
            for data in chapter_link_list:
                name, link = data.decode('utf8').split('---')
                name_list.append(name)
                link_list.append(link)
            # 将获取到的 link 和 name 按顺序 插入 redis中
            redis_cli.rpush('%s_chapters_link' % comic_name, *link_list)
            redis_cli.rpush('%s_chapters_name' % comic_name, *name_list)
            redis_cli.delete('%s_error_url' % comic_name)
        else:
            get_comic_chapter_links(
                    browser=browser,
                    link=url,
                    comic_name=comic_name,
                    end=-20, step=-1
                    )
            chapter_link_list = redis_cli.lrange(
                    '%s_chapters_link' % comic_name, 0, -1)
    print("test: ", redis_cli.lrange('%s_chapters_link' % comic_name, 0, -1))
    while True:
        # 获取 章节的名字
        link = redis_cli.lpop('%s_chapters_link' % comic_name)
        if not link:
            print("所有章节 下载完成")
            break
        link = link.decode('utf8')

        chapter_name = redis_cli.lpop(
                '%s_chapters_name' % comic_name).decode('utf8')
        # 提前将 url 加入 error_url 查询成功后再删除
        redis_cli.rpush(
                '%s_error_url' % comic_name, '%s---%s' % (chapter_name, link))
        print('spider begin crawer ', link)
        print('爬去的章节名字: ', chapter_name)
        # 下载图片
        is_download_success = get_fzdm_img(
                browser, link, chapter_name, comic_name)
        # 如果下载图片成功 则删除错误url
        if is_download_success:
            redis_cli.lpop('%s_error_url' % comic_name)
    browser.close()


if __name__ == '__main__':
    url = 'https://manhua.fzdm.com/10/'
    comic_name = 'hunter'
    # comic_name = input('保存的目录名字: ')
    main(url, comic_name, None)
