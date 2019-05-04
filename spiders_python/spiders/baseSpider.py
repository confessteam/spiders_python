#!/usr/bin/python
# -*- coding: utf-8 -*-

## zara抓取程序，需要输入版本号 scrapy crawl zara -a taskId=1

import scrapy
import re
import json
import base64
import time
import copy
import sys
import traceback
import logging
import pdb
import urllib
import hashlib
import os

from scrapy import log
from scrapy.utils.project import get_project_settings

from spiders_python.commonTools import common
from spiders_python.items import ConfessItem

settings = get_project_settings()
IMAGES_STORE = settings.get("IMAGES_STORE")


class baseSpider(scrapy.Spider):
    taskId = -1
    taskType = ''
    env_type = "offline"

    parsePage = 'call_url'
    RETRY_TIMES = -5

    MAX_RETRY = 3
    MAX_RETRY_TOTAL = 1000
    _retryItemMap = {}
    _retryTimes = 0
    requestPriority = -10
    extra_urls = []

    # 扩展属性
    errorLogCount = 0

    sourceUrls = '[]'

    # 自己添加代码
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        absPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(absPath, "log/currentLog.txt")
        with open(path, 'w') as f:
            f.truncate()
        spider = cls(*args, **kwargs)
        spider._set_crawler(crawler)
        return spider

    def start_requests(self):
        product_info = {}
        cookiejar = 1
        if self.taskType == 'spider_update':
            sourceUrlList = json.loads(self.sourceUrls)
            for url in sourceUrlList:
                product_info['product_url'] = url
                request = scrapy.Request(url, callback=self.get_product_info)
                request.meta['product_info'] = copy.deepcopy(product_info)
                request.meta['retry_times'] = -10
                request.dont_filter = True
                request.meta['cookiejar'] = cookiejar
                yield request
                cookiejar = cookiejar + 1
        else:
            for request_url in self.start_urls:
                request = scrapy.Request(request_url, callback=self.call_url)
                request.meta['product_info'] = copy.deepcopy(product_info)
                request.meta['parsePage'] = self.parsePage
                request.meta['retry_times'] = -10
                request.dont_filter = True
                request.meta['cookiejar'] = cookiejar
                yield request
                cookiejar = cookiejar + 1

    # def get_source_url(self, taskId):
    #     logging.info('get_task_info %s' % taskId)
    #     url = '/api/task/getTaskById'
    #     postData = {
    #         'taskId': taskId,
    #     }
    #     ret = self.commonLib.http_post(url, postData)
    #     retData = json.loads(ret)
    #     if retData['errno'] != 0 or not retData['data']:
    #         logging.warning("getTaskById failed and ret is [%s]" % (ret))
    #     else:
    #         taskInfo = retData['data']
    #         taskExtra = json.loads(taskInfo['extra'])
    #         if taskExtra.get('sourceUrlList', ''):
    #             self.extra_urls.extend(taskExtra['sourceUrlList'].split('\n'))

    # def retry_url(self, product_info):
    #     url = product_info['product_url']
    #     parsePage = product_info['parsePage']
    #     self._retryTimes = self._retryTimes + 1
    #     self._retryItemMap[url] = self._retryItemMap.get(url, 0) + 1
    #     logging.warning("get_product_info failed retry to crawl item of [%s] in task [%s] , retry time is [%s]" % (
    #         url, self.taskId, self._retryItemMap[url]))
    #
    #     if self._retryTimes >= self.MAX_RETRY_TOTAL:
    #         raise ValueError("spider beyond max total retry [%s]" % (url))
    #
    #     if self._retryItemMap[url] <= self.MAX_RETRY:
    #         itemInfoList = []
    #         urlInfo = {
    #             "itemType": common.TYPE_URL,
    #             "item": url,
    #             "product_info": copy.deepcopy(product_info),
    #             "parsePage": parsePage,
    #             "dont_filter": True
    #         }
    #         itemInfoList.append(urlInfo)
    #         return itemInfoList
    #     else:
    #         raise ValueError("url is beyond max retry [%s]" % (url))

    def parse(self, response):
        logging.info('parse of [%s]', response.meta)

    def get_text_list(self, response, xpath, urljoin=False):
        infoList = []
        for option in response.xpath(xpath):
            option = option.extract().strip()
            if option:
                if urljoin == True:
                    option = response.urljoin(option)
                infoList.append(option)
        return infoList

    def call_url(self, response):
        # logging.info('call_url of [%s],meta is [%s]',response.url,response.meta)
        try:
            parsePage = response.meta['parsePage']
            itemInfoList = getattr(self, parsePage)(response)
            if not itemInfoList:
                return
            for urlInfo in itemInfoList:
                # logging.info('get urlInfo is [%s]',urlInfo)
                itemType = urlInfo.get("itemType")
                cookies = urlInfo.get("cookies", None)
                product_info = copy.deepcopy(urlInfo.get("product_info"))
                cookiejar = ''
                if product_info and product_info.get('cookiejar', ''):
                    cookiejar = product_info.get('cookiejar', '')
                if itemType == common.TYPE_URL:
                    dont_filter = urlInfo.get("dont_filter", False)
                    request = scrapy.Request(urlInfo['item'], cookies=cookies, dont_filter=dont_filter,
                                             callback=self.call_url)
                    request.meta['product_info'] = product_info
                    request.meta['parsePage'] = urlInfo.get("parsePage")
                    request.meta['retry_times'] = self.RETRY_TIMES
                    if cookiejar:
                        request.meta['cookiejar'] = cookiejar
                    if product_info and product_info.get('dont_filter') == True:
                        request.dont_filter = True
                    if product_info and product_info.get('priority'):
                        request.priority = product_info.get('priority')
                    yield request
                elif itemType == common.TYPE_CONFESS:
                    confessItem = ConfessItem()
                    for key, value in urlInfo['item'].items():
                        confessItem[key] = value
                    yield confessItem
                elif itemType == common.TYPE_REQUEST:
                    request = urlInfo['item']
                    request.callback = self.call_url
                    request.meta['product_info'] = product_info
                    request.meta['parsePage'] = urlInfo.get("parsePage")
                    request.meta['retry_times'] = self.RETRY_TIMES
                    if cookiejar:
                        request.meta['cookiejar'] = cookiejar
                    yield request
        except Exception as e:
            msgStr = json.dumps(traceback.format_exc())
            logging.warning(msgStr)

            # 自己添加功能
            absPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(absPath, "log/currentLog.txt")
            msgStrList = msgStr.split("\\n")
            with open(path, 'a') as f:
                self.errorLogCount += 1
                f.write(("*" * 20 + "第%d条" + "*" * 20 + "\n") % self.errorLogCount)
                for msgS in msgStrList:
                    f.write(msgS)
                    f.write('\n')
                f.write("\n\n\n\n")

    def downloadPic(self, picUrl):
        logging.info('downloadPic, picUrl %s' % (picUrl))
        fileName = hashlib.md5(picUrl).hexdigest() + '.jpg'
        filePath = IMAGES_STORE + "full/" + fileName
        if os.path.isfile(filePath):
            logging.info('picUrl %s, download done' % picUrl)
            ret = self.uploadPic(picUrl, filePath)
        else:
            try:
                result = urllib.urlretrieve(picUrl, filePath)
            except urllib.ContentTooShortError:
                logging.warning(
                    'retry, download fail,picUrl  %s, error msg %s' % (picUrl, urllib.ContentTooShortError.message))
                result = urllib.urlretrieve(picUrl, filePath)
            logging.info('downloadPic result is %s' % result[0])
            if os.path.isfile(result[0]):
                ret = self.uploadPic(picUrl, result[0])
            else:
                ret = self.uploadPic(picUrl, common.STATUS_FAIL)
        logging.info('uploadPic ret %s' % json.dumps(ret))
        return ret

    def uploadPic(self, picUrl, picPath):
        logging.info('uploadPic picUrl is %s, picPath %s' % (picUrl, picPath))
        url = '/api/spider/uploadPic'
        post_data = {
            'picUrl': picUrl,
            'picPath': picPath,
        }
        ret = self.commonLib.http_post(url, post_data)
        logging.info('uploadPic ret %s' % (ret))
        data = json.loads(ret)
        if data['errno'] != 0:
            logging.warning('upload pic Fail')
            return {}
        fkey = data['data']['picKey']
        qiniuUrl = 'https://pic.bbtkids.cn/%s' % fkey
        return {'fkey': fkey, 'qiniuUrl': qiniuUrl}
