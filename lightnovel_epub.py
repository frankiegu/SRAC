#!/usr/bin/env python
# -*- coding: utf-8 -*-

# lightnovel - lightnovel_epub.py
# Created by JT on 13-Nov-18 10:17.
# Blog: https://blog.jtcat.com/
# 
# author = 'JT <jiting@jtcat.com>'

import re
import time
import json
import getpass
from selenium import webdriver


def login():
    print("登录", end=' -> ')
    try:
        cookies = json.loads(getpass.getpass("请黏贴轻国cookies或直接回车跳过(无回显):"))
        if not cookies:
            cookies = None
    except json.decoder.JSONDecodeError:
        print("无效cookies，使用QQ登录")
        print("建议：请确保cookies格式为紧凑json(在同一行内)")
        cookies = None
    if not cookies:
        driver.get("https://www.lightnovel.cn/")
        time.sleep(2)

        driver.find_element_by_xpath('//*[@id="lsform"]/div/div[2]/p[1]/a').click()
        time.sleep(2)

        driver.switch_to.frame("ptlogin_iframe")
        driver.execute_script('document.getElementById("qlogin").style="display: none;"')
        driver.execute_script('document.getElementsByClassName("authLogin").style="display: none;"')
        driver.execute_script('document.getElementById("web_qr_login").style="display: block;"')
        time.sleep(1)

        driver.find_element_by_name("u").clear()
        driver.find_element_by_name("u").send_keys(str(input("请输入QQ号:")))
        driver.find_element_by_name("p").clear()
        driver.find_element_by_name("p").send_keys(str(getpass.getpass("请输入密码(无回显):")))
        driver.find_element_by_id("login_button").click()
        time.sleep(4)
    else:
        driver.get("https://www.lightnovel.cn/")
        time.sleep(3)
        driver.delete_all_cookies()
        for x in cookies:
            driver.add_cookie(x)
    driver.get("https://www.lightnovel.cn/")
    time.sleep(2)
    if not login_check():
        print('失败')
        driver.close()
        exit()
    else:
        print('登录成功')


def login_check():
    try:
        status = driver.find_element_by_xpath('//*[@id="lsform"]/div/div[1]/table/tbody/tr[2]/td[3]/button').text
    except Exception as err:
        assert 'Unable to locate element' in str(err)
        status = driver.find_element_by_xpath('//*[@id="um"]/p[1]/a[5]').text
        if status == '退出':
            return True
        else:
            print('发生了意外情况')
            driver.close()
            exit()
    if status == '登录':
        return False


def load_data(import_data=None):
    print("从文件读取现有数据", end=' -> ')
    if import_data:
        tmp = import_data
    else:
        tmp = []
    try:
        with open("lightnovel_epub.json", "r", encoding='utf-8') as f:
            tmp += json.load(f)
        print('成功')
    except FileNotFoundError:
        print('现有数据不存在，跳过')
    return tmp


def save_data(thread_info):
    print("写入数据到文件", end=' -> ')
    if thread_info:
        with open("lightnovel_epub.json", "w", encoding='utf-8') as f:
            json.dump(thread_info, f, sort_keys=True, indent=4, ensure_ascii=False)
        print('成功')
    else:
        print('无数据输入')


def get_download_info():
    all_links = driver.find_elements_by_xpath('//a[contains(@href, "baidu.com/s")]')
    if len(all_links) >= 1:  # 获取百度云分享
        info = []
        for x in all_links:
            print(driver.title[:-30])
            dl_link = x.get_attribute('href')
            print('链接: ', dl_link)
            dl_link_description = x.find_element_by_xpath('..').text \
                if len(x.find_element_by_xpath('..').text) <= 60 else x.text
            dl_text = driver.title[:-30] if x.text == dl_link else dl_link_description
            code = find_code(dl_link_description, dl_link)
            if code:
                info.append({'link': dl_link, 'title': dl_text, 'code': code})
            else:
                info.append({'link': dl_link, 'title': dl_text})
        return info
    else:
        pass  # TODO 论坛附件及其他网盘下载方式
        return []


def find_code(dl_link_description, dl_link):
    post_massage = driver.find_element_by_xpath('//*[starts-with(@id, "postmessage")]')
    post_massage_list = post_massage.text.split("\n")
    for y in post_massage_list:
        if dl_link_description in y:
            code = re.findall("(?!epub)(?!\d+MB)([a-zA-Z0-9]{4})", y)
            if len(code) == 0:
                print("未找到提取码")
                return []
            else:
                code = code[-1]
                if code in dl_link:
                    print('似乎没有提取码', code)
                    return []
                else:
                    print('提取码: ', code)
                    return code
    return []


def get_thread(thread_info, last_page=None):
    forum_entrance = driver.find_element_by_xpath('//*[@id="category_3"]/table/tbody/tr[3]/td[2]/p[1]/a[2]')
    base_url = forum_entrance.get_attribute('href')[:-6]
    forum_entrance.click()
    time.sleep(2)
    if not last_page:
        last_page = int(
            re.search("([\d]+)", driver.find_element_by_xpath('//*[@id="fd_page_bottom"]/div/a[10]').text).group(0))
    elif last_page <= 1:
        last_page = 1
    time.sleep(1)
    for i in range(1, last_page + 1):
        print('获取第 %s 页信息' % i)
        driver.get(base_url + "%s%s" % (i, '.html'))
        time.sleep(1.2)
        thread_info = add_thread_info(thread_info)
    return thread_info


def add_thread_info(thread_info):
    thread_list = driver.find_elements_by_xpath('//*[contains(@id, "normalthread")]')
    for x in range(len(thread_list)):
        thread = thread_list[x].find_element_by_xpath('./tr/th/a[2]')
        link = str(thread.get_attribute('href'))
        title = thread.text
        add = True if link[:-8] not in [s['link'][:-8] for s in thread_info] or len(thread_info) == 0 else False
        if add:
            print("添加", title)
            if '查水线' in title:
                print("检查到查水线，跳过")
                continue
            thread_info.append({'title': title, 'link': link})
    return thread_info


def get_thread_info():
    for i in range(len(data)):
        driver.get(data[i]['link'])
        time.sleep(0.3)
        download_info = get_download_info()
        if len(download_info) == 0:
            print('暂无资源信息')
            download_info = 'Unknown'
        data[i]['download'] = download_info


if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    # options.binary_location = '/Applications/Google Chrome'  # 指定 chrome 可执行文件位置
    options.add_argument('headless')  # 无窗口模式
    options.add_argument('log-level=2')
    # options.add_argument('start-maximized')  # 最大化窗口
    driver = webdriver.Chrome(chrome_options=options)
    # data = []
    data = load_data()  # 加载初始化数据
    try:
        login()
        # search link
        pages = int(input('请输入要获取信息的页数(全部获取请直接回车): ')) or None
        data = get_thread(data, pages)
        save_data(data)
        # get_thread_info()
        # save_data(data)
    except Exception as e:
        print(e)
    finally:
        save_data(data)
        driver.close()
