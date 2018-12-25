# coding: utf8

import os
import json
from datetime import datetime

import requests
from lxml import etree

from tools import compare
from send_email import send_email


url = 'https://www.piaotian.com/html/9/9054/'
a_xpath = '//div/ul/li/a'
chpt_xpath = './body/text()'
TIME_FORMAT = "%Y/%m/%d"


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
    with open(noval_filename, 'a') as f:
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
        chpt_url = chapter.xpath("./@href")
        chpt_name = chapter.xpath("./text()")
        chpt_infos.append([chpt_url, chpt_name])

    # 对比并保存新的 小说章节
    title = html.xpath("//div[@class='title']")
    if title:
        save_filename = title[0] + '.json'
    else:
        title = url.split('/')[-1]

    # 查询新章节
    if os.path.exists(save_filename):
        with open(save_filename, 'r') as info_f:
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

            # send email to user
            send_email(noval_filename)
            # 删除
            os.remove(noval_filename)

        with open(save_filename, 'w') as f:
            chpt_json = json.dumps(chpt_infos)
            f.write(chpt_json)


if __name__ == "__main__":
    if os.path.exists('novals.json'):
        with open('./novals.json', 'w') as f:
            noval_urls = json.loads(f.read())
            for url in noval_urls:
                check_new_chapters(url)
