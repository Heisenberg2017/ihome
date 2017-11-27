# coding:utf-8

import logging
from .BaseHandler import BaseHandler
from utils.response_code import RET
import json
import constants
from utils.commons import required_login
import config
from utils.qiniu_storage import storage


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
            return self.write({"errcode":RET.DBERR,"errmsg":"get data err"})
        houses = []
        print result
        if result:
            for l in result:

                house = {
                    "house_id":l["hi_house_id"],
                    "title":l["hi_title"],
                    "price": l["hi_price"],
                    "ctime":l["hi_ctime"].strftime("%Y-%m-%d"),
                    "area_name":l["ai_name"],
                    "img_url":config.image_domain+l["hi_index_image_url"] if l["hi_index_image_url"] else ""
                }
                houses.append(house)
        self.write({"errcode": RET.OK,"errmsg":"OK", "houses":houses})


class HouseInfoHandler(BaseHandler):

    @required_login
    def post(self):
        print self.json_dict
        user_id = self.session.data["up_user_id"]
        print user_id
        title = self.json_dict.get("title")
        price = self.json_dict.get("price")
        area_id = self.json_dict.get("area_id")
        address = self.json_dict.get("address")
        room_count = self.json_dict.get("room_count")
        acreage = self.json_dict.get("acreage")
        unit = self.json_dict.get("unit")
        capacity = self.json_dict.get("capacity")
        beds = self.json_dict.get("beds")
        deposit = self.json_dict.get("deposit")
        min_days = self.json_dict.get("min_days")
        max_days = self.json_dict.get("max_days")
        facility = self.json_dict.get("facility")
        # 校验用户传入信息是否传入
        if not all((title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days,
                    max_days,facility)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="缺少参数"))
        try:
            price = int(price)*100
            deposit = int(deposit)*100
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.PARAMERR, errmsg="参数错误"))

        # 数据
        try:
            sql = "insert into ih_house_info(hi_user_id,hi_title,hi_price,hi_area_id,hi_address,hi_room_count," \
                  "hi_acreage,hi_house_unit,hi_capacity,hi_beds,hi_deposit,hi_min_days,hi_max_days) " \
                  "values(%(user_id)s,%(title)s,%(price)s,%(area_id)s,%(address)s,%(room_count)s,%(acreage)s," \
                  "%(house_unit)s,%(capacity)s,%(beds)s,%(deposit)s,%(min_days)s,%(max_days)s)"

            house_id = self.db.execute(sql, user_id=user_id, title=title, price=price, area_id=area_id, address=address,
                                       room_count=room_count, acreage=acreage, house_unit=unit, capacity=capacity,
                                       beds=beds, deposit=deposit, min_days=min_days, max_days=max_days)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="save data error"))

        try:
            sql = "insert into ih_house_facility(hf_house_id,hf_facility_id) values"
            sql_val = []
            vals = []
            for facility_id in facility:
                sql_val.append("(%s, %s)")
                vals.append(house_id)
                vals.append(facility_id)

            sql += ",".join(sql_val)  # (%s, %s),(%s, %s),(%s, %s)...
            vals = tuple(vals)  # (house_id,facility_id,house_id,facility_id,house_id,facility_id...)
            logging.debug(sql)
            logging.debug(vals)
            self.db.execute(sql, *vals)
        except Exception as e:
            logging.error(e)
            try:
                self.db.execute("delete from ih_house_info where hi_house_id=%s", house_id)
            except Exception as e:
                logging.error(e)
                return self.write(dict(errcode=RET.DBERR, errmsg="delete fail"))
            else:
                return self.write(dict(errcode=RET.DBERR, errmsg="no data save"))
                # 返回
        self.write(dict(errcode=RET.OK, errmsg="OK", house_id=house_id))


class HouseImageHandler(BaseHandler):
    """"""
    @required_login
    def post(self):
        house_id = self.get_argument('house_id')
        if not house_id:
            return self.write("")
        try:
            image_data = self.request.files['house_image'][0]['body']
        except Exception as e:
            # 参数出错
            logging.error(e)
            return self.write("")
        try:
            key = storage(image_data)
        except Exception as e:
            logging.error(e)
            return self.write("")

        print key
        # 更新房屋图片url到数据库内
        try:
            self.db.execute("update ih_house_info set hi_index_image_url = %(index_image_url)s where hi_house_id  = %(house_id)s", index_image_url=key, house_id=house_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库出错"))

        # 更新session
        self.session.data['hi_index_image_url'] = key
        self.session.save()

        data = config.image_domain+key
        self.write(dict(errcode=RET.OK, url=data))
