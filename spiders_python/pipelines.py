# -*- coding: utf-8 -*-
import pdb

import requests
import scrapy
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem

from spiders_python.commonTools.common import OK, CONFESS
from spiders_python.settings import CONFESS_POST_URL


class AllTypeItemPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if not item.get('image_urls'):
            return
        for image_url in item['image_urls']:
            yield scrapy.Request(image_url)

    def item_completed(self, results, item, info):
        itemType = item.itemType
        if itemType == CONFESS:  # item为product时的处理
            image_paths = [x['path'] for ok, x in results if ok]
            if not image_paths:
                raise DropItem("Item contains no images")
            item['image_paths'] = image_paths
            data = {}
            for key, value in item.items():
                data[key] = value
            res = requests.post(CONFESS_POST_URL, data=data)
            pdb.set_trace()
            if res.code != OK:
                # raise RuntimeError('message:commit data fail***url:%s***item:%s' % (CONFESS_POST_URL, item.toStr()))
                pass
        # elif itemType == '指定类型':  # item为图片时的处理
        #     image_paths = [x['path'] for ok, x in results if ok]
        #     if not image_paths:
        #         raise DropItem("Item contains no images")
        #     item['image_paths'] = image_paths
        return item
