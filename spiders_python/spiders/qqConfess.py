# -*- coding: utf-8 -*-
import scrapy


class QqconfessSpider(scrapy.Spider):
    name = 'qqConfess'
    allowed_domains = ['qq.com']
    start_urls = ['http://qq.com/']

    def parse(self, response):
        pass
