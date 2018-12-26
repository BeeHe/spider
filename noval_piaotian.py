# coding: utf8

import os
import json
from datetime import datetime

import requests
from lxml import etree

from tools import compare
from send_email import send_email


basedir = os.path.abspath(os.path.dirname(__file__))
url = 'https://www.piaotian.com/html/9/9054/'
a_xpath = '//div/ul/li/a'
chpt_xpath = './body/text()'
TIME_FORMAT = "%Y_%m_%d"


def request_get(url, xpath):
    resp = requests.get(url)
    if resp.ok:
        html = etree.fromstring(resp.text, etree.HTMLParser())
        element = html.xpath(xpath)
        return html, element


def download_chapter(title, url):
    """download chapter"""
    # get noval and save
    html, atricle_lines = request_get(url, chpt_xpath)
    article = ''.join([line.replace('\xa0', '') for line in atricle_lines])

    now = datetime.now()
    noval_filename = title + '-' + now.strftime(TIME_FORMAT)
    noval_path = os.path.join(basedir, noval_filename)
    with open(noval_path, 'a') as f:
        f.write(article)
    return noval_filename


def check_new_chapters(url):
    """check if there is new chapter and
    save new chapters in json form into noval.json
    """

    html, chapters = request_get(url, a_xpath)
    # 获取章节
    chpt_infos = []
    for chapter in chapters:
        chpt_url = chapter.xpath("./@href")[0]
        chpt_name = chapter.xpath("./text()")[0]
        chpt_infos.append([chpt_url, chpt_name])

    # 对比并保存新的 小说章节
    title = html.xpath("//div[@class='title']/h1/text()")
    if title:
        title = title[0]
        save_filename = title + '.json'
    else:
        title = url.split('/')[-1]
        save_filename = title + '.json'
    save_path = os.path.join(basedir, save_filename)
    print(save_path)

    # 查询新章节
    if os.path.exists(save_path):
        with open(save_path, 'r') as info_f:
            old_chpt_infos = json.loads(info_f.read())
        new_chpt_infos = compare(old=old_chpt_infos, new=chpt_infos)

        # todo: download chapter according to new_chpt_infos
        if new_chpt_infos:
            for chpt_url, chpt_name in new_chpt_infos:
                # 查看url 是否以 '/' 结尾
                base_url = url.split('index.html')[0]
                if base_url[-1] == '/':
                    chapter_link = base_url + chpt_url
                else:
                    chapter_link = base_url + '/' + chpt_url
                noval_filename = download_chapter(title, chapter_link)
                noval_path = os.path.join(basedir, noval_filename)

            # send email to user
            send_email(noval_path)
            # 删除
            os.remove(noval_path)

    with open(save_path, 'w') as f:
        chpt_json = json.dumps(chpt_infos)
        f.write(chpt_json)


if __name__ == "__main__":
    urls_file = 'novals.json'
    urls_path = os.path.join(basedir, urls_file)
    print(urls_path)
    if os.path.exists(urls_path):
        with open(urls_path, 'r') as f:
            noval_urls = json.loads(f.read())
            for url in noval_urls:
                check_new_chapters(url)
