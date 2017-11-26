# coding:utf-8

import logging
from .BaseHandler import BaseHandler
from utils.response_code import RET
import json
import constants
from utils.commons import required_login
import config


class AreaInfoHandler(BaseHandler):
    """提供城区信息"""
    def get(self):

        # 从reids中取出地区信息
        try:
            areas_data = self.redis.get("area_info")
        except Exception as e:
            logging.error(e)
            areas_data = None
        # redis中地区信息不为空
        if areas_data:
            logging.info("hit redis: area_info")
            resp = '{"errcode":"0","errmsg":"OK","areas":%s}'% areas_data
            print resp
            return self.write(resp)
        # redis中无区域信息，查询数据库
        try:
            areas_data = self.db.query("select ai_area_id,ai_name from ih_area_info")
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="get data error"))
        # 数据库中地区信息为空
        if not areas_data:
            return self.write(dict(errcode=RET.NODATA, errmsg="no area data"))
        # 取出数据库中地区信息
        areas = []
        for l in areas_data:
            area = {
                "area_id":l["ai_area_id"],
                "name":l["ai_name"]
            }
            areas.append(area)

        # 返回给用户数据前，往redis保存一份
        json_data = json.dumps(areas)
        try:
            self.redis.setex("area_info", constants.REDIS_AREA_INFO_EXPIRES_SECONDS,json_data)
        except Exception as e:
            logging.error(e)

        self.write(dict(errcode=RET.OK, errmsg="OK", areas=areas))


class MyHousesHandler(BaseHandler):
    """提供房屋信息"""
    @required_login
    def get(self):
        user_id = self.session.data["up_user_id"]
        try:
            result = self.db.query("select a.hi_house_id,a.hi_title,a.hi_price,a.hi_ctime,b.ai_name,a.hi_index_image_url "\
                                   "from ih_house_info a "\
                                   "left join ih_area_info b on a.hi_area_id=b.ai_area_id where a.hi_user_id=%s;", user_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errno":RET.DBERR,"errmsg":"get data err"})
        houses = []
        if result:
            for l in result:
                house = {
                    "house_id":l["hi_house_id"],
                    "title":l["hi_title"],
                    "price":l["hi_ctime"].strftime("%Y-%m-%d"),
                    "area_name":l["ai_name"],
                    "img_url":config.image_domain+l["hi_index_image_url"] if l["hi_index_image_url"] else ""
                }

                houses.append(houses)
        self.write({"error": RET.OK,"errmsg":"OK", "houses":houses})

class HouseInfoHandler(BaseHandler):
    def post(self):
        print self.json_dict
