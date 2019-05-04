# -*- coding: utf-8 -*-
import copy
import pdb

import scrapy

from spiders_python.commonTools import common
from spiders_python.items import ConfessItem
from spiders_python.spiders.baseSpider import baseSpider


class QqconfessSpider(baseSpider):
    name = 'qqConfess'
    allowed_domains = ['fand.wang']
    start_urls = ['http://www.fand.wang/']
    parsePage = 'myparse'

    def myparse(self, response):
        productInfo = response.meta.get('product_info')
        itemInfoList = []
        imagesList = response.xpath('//img/@src').extract()
        confessItem = ConfessItem()
        confessItem['userId'] = 1
        confessItem['context'] = '我是你爸爸'
        confessItem['userName'] = 1
        confessItem['image_urls'] = imagesList
        urlInfo = {
            'itemType': common.TYPE_CONFESS,
            'item': confessItem,
            'product_info': copy.deepcopy(productInfo)
        }
        itemInfoList.append(urlInfo)
        return itemInfoList



