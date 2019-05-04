# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy

from spiders_python.commonTools.common import CONFESS


class BaseItem(scrapy.Item):
    def toStr(self):
        str = ''
        for key, value in self.items():
            str += '%s:%s,' % (key, value)
        return str


class ConfessItem(BaseItem):
    itemType = CONFESS
    userId = scrapy.Field()
    context = scrapy.Field()
    userName = scrapy.Field()
    image_urls = scrapy.Field()
    image_paths = scrapy.Field()

