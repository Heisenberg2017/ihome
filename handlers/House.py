# coding:utf-8

import logging
from .BaseHandler import BaseHandler
from utils.response_code import RET
import json
import constants
from utils.commons import required_login
import config
from utils.qiniu_storage import storage
from utils.session import Session
import math

class IndexHandler(BaseHandler):

    """首页信息"""
    def get(self):

        # 从reids中取出地区信息
        try:
            areas_data = self.redis.get("area_info")
        except Exception as e:
            logging.error(e)
            areas_data = None
        # redis没有地区信息,查询数据库
        if not areas_data:
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
                    "area_id": l["ai_area_id"],
                    "name": l["ai_name"]
                }
                areas.append(area)
            # 往redis保存一份地区信息
            areas_data = json.dumps(areas)
            print("areas_data:%s"%areas_data)
            try:
                self.redis.setex("area_info", constants.REDIS_AREA_INFO_EXPIRES_SECONDS, areas_data)
            except Exception as e:
                logging.error(e)
        else:
            logging.info("hit redis: area_info")
            print("areas_data:%s" % areas_data)
        # 此处需保证无论从mysql或者redis获得的areas_data必须完全相同(json字符串)
        # redis查询是否有房屋信息
        try:
            houses_data = self.redis.get("index_houses_info")
        except Exception as e:
            logging.error(e)
            houses_data = None
        # redis中有房屋信息，返回数据
        if houses_data:
            logging.info("hit redis: index_houses_info")
            resp = '{"errcode":"0","errmsg":"OK","areas":%s,"houses":%s}'% (areas_data,houses_data)
            print resp
            return self.write(resp)

        # redis中无房屋信息,数据库查询
        try:
            houses_data = self.db.query("select hi_house_id,hi_title,hi_index_image_url from ih_house_info order by"\
                                        " hi_order_count desc limit %s;"% constants.INDEX_PAGE_MAX_HOUSES_NUMBER)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="get data error"))

        houses = []
        for l in houses_data:
            house = {
                "house_id":l["hi_house_id"],
                "title":l["hi_title"],
                "img_url": config.image_domain+l["hi_index_image_url"]
            }
            houses.append(house)
        # 放入缓存中
        houses_data = json.dumps(houses)
        try:
            self.redis.setex("index_houses_info", constants.REDIS_INDEX_HOUSES_INFO_SECONDS,houses_data)
        except Exception as e:
            logging.error(e)
        # 返回数据
        resp = '{"errcode":"0","errmsg":"OK","areas":%s,"houses":%s}' % (areas_data, houses_data)
        print resp
        return self.write(resp)


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
    # 需要获得的数据
    # data = {"images": ["http://ozyfrfdcg.bkt.clouddn.com/FoZg1QLpRi4vckq_W3tBBQe1wJxn",
    #                    "http://ozyfrfdcg.bkt.clouddn.com/FoZg1QLpRi4vckq_W3tBBQe1wJxn",
    #                   "http://ozyfrfdcg.bkt.clouddn.com/FoZg1QLpRi4vckq_W3tBBQe1wJxn"],
    #         "price": "100",
    #         "title": "测试专用",
    #         "user_name": "老王测试",
    #         "address": "厦门湖里区鼓浪屿",
    #         "room_count": "3",
    #         "acreage": "100",
    #         "unit": "5",
    #         "capacity": "10",
    #         "beds": "3",
    #         "deposit": "1000",
    #         "min_days": "1",
    #         "max_days": "0",
    #         "facilities": [1, 3, 5, 7],
    #         "user_avatar": "http://ozyfrfdcg.bkt.clouddn.com/FuXUPWubefYhFsyPOBeALH3F3Fts",
    #         "comments": [
    #             {"user_name": "测试号",
    #             "ctime": "2017-10-3",
    #             "content": "房子很棒我很喜欢",},
    #           ]
    #         }
    def get(self):
        house_id = self.get_argument('house_id')
        self.session = Session(self)
        user_id = self.session.data.get("up_user_id", "-1")
        print house_id

        if not house_id:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="缺少参数"))

            # 先从redis缓存中获取信息
        try:
            result = self.redis.get("house_info_%s" % house_id)
        except Exception as e:
            logging.error(e)
            result = None
        if result:
            # 此时从redis中获取到的是缓存的json格式数据
            resp = '{"errcode":"0", "errmsg":"OK", "data":%s, "user_id":%s}' % (result, user_id)
            return self.write(resp)

            # 查询数据库

            # 查询房屋基本信息
        sql = "select hi_title,hi_price,hi_address,hi_room_count,hi_acreage,hi_house_unit,hi_capacity,hi_beds," \
              "hi_deposit,hi_min_days,hi_max_days,up_name,up_avatar,hi_user_id " \
              "from ih_house_info left join ih_user_profile on hi_user_id=up_user_id where hi_house_id=%s"

        try:
            result = self.db.get(sql, house_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="查询错误"))

        # 用户查询的房屋id不存在
        if not result:
            return self.write(dict(errcode=RET.NODATA, errmsg="查无此房"))

        data = {
            "hid": house_id,
            "user_id": result["hi_user_id"],
            "title": result["hi_title"],
            "price": result["hi_price"],
            "address": result["hi_address"],
            "room_count": result["hi_room_count"],
            "acreage": result["hi_acreage"],
            "unit": result["hi_house_unit"],
            "capacity": result["hi_capacity"],
            "beds": result["hi_beds"],
            "deposit": result["hi_deposit"],
            "min_days": result["hi_min_days"],
            "max_days": result["hi_max_days"],
            "user_name": result["up_name"],
            "user_avatar": config.image_domain + result["up_avatar"] if result.get("up_avatar") else ""
        }

        # 查询房屋的图片信息
        sql = "select hi_url from ih_house_image where hi_house_id=%s"
        try:
            result = self.db.query(sql, house_id)
        except Exception as e:
            logging.error(e)
            result = None

        # 如果查询到的图片
        images = []
        if result:
            for image in result:
                images.append(config.image_domain + image["hi_url"])
        data["images"] = images

        # 查询房屋的基本设施
        sql = "select hf_facility_id from ih_house_facility where hf_house_id=%s"
        try:
            result = self.db.query(sql, house_id)
        except Exception as e:
            logging.error(e)
            result = None

        # 如果查询到设施
        facilities = []
        if result:
            for facility in result:
                facilities.append(facility["hf_facility_id"])
        data["facilities"] = facilities

        # 查询评论信息
        sql = "select oi_comment,up_name,oi_utime,up_mobile from ih_order_info left join ih_user_profile " \
              "on oi_user_id=up_user_id where oi_house_id=%s and oi_status=4 and oi_comment is not null"

        try:
            result = self.db.query(sql, house_id)
        except Exception as e:
            logging.error(e)
            result = None
        comments = []
        if result:
            for comment in result:
                comments.append(dict(
                    user_name=comment["up_name"] if comment["up_name"] != comment["up_mobile"] else "匿名用户",
                    content=comment["oi_comment"],
                    ctime=comment["oi_utime"].strftime("%Y-%m-%d %H:%M:%S")
                ))
        data["comments"] = comments

        # 存入到redis中
        json_data = json.dumps(data)
        try:
            self.redis.setex("house_info_%s" % house_id, constants.REDIS_HOUSE_INFO_EXPIRES_SECONDES,
                             json_data)
        except Exception as e:
            logging.error(e)
        # json格式的数据直接进行拼接字符串发送给前端
        resp = '{"errcode":"0", "errmsg":"OK", "data":%s, "user_id":%s}' % (json_data, user_id)
        # self.write(dict(errcode=RET.OK, errmsg="OK", data=data))
        self.write(resp)
        # self.write({"errcode":RET.OK,"data":data})
    @required_login
    def post(self):
        user_id = self.session.data["up_user_id"]
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
        sql = "insert into ih_house_image(hi_house_id,hi_url) values(%s,%s);" \
                  "update ih_house_info set hi_index_image_url=%s " \
                  "where hi_house_id=%s and hi_index_image_url is null;"

        try:
            self.db.execute(sql,house_id,key,key,house_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="数据库出错"))

        # 更新session
        self.session.data['hi_index_image_url'] = key
        self.session.save()

        data = config.image_domain+key
        self.write(dict(errcode=RET.OK, url=data))


class SearchHandler(BaseHandler):

    def get(self):
        # 获取参数
        start_date = self.get_argument("sd", "")
        end_date = self.get_argument("ed", "")
        area_id = self.get_argument("aid", "")
        sort_key = self.get_argument("sk", "new")
        page = int(self.get_argument("p", "1"))

        # 查询redis中匹配房屋信息列表
        try:
            redis_key = "houses_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
            ret = self.redis.hget(redis_key, page)
        except Exception as e:
            logging.error(e)
            ret = None
        # 返回redis中的数据
        if ret:
            logging.info("hit redis")
            return self.write(ret)

        # 无缓存数据，根据用户条件做查询
        # 所需查询房屋信息的sql语句
        sql = "select distinct hi_title,hi_house_id,hi_price,hi_room_count,hi_address,hi_order_count,up_avatar,hi_index_image_url,hi_ctime" \
              " from ih_house_info left join ih_user_profile on hi_user_id=up_user_id left join ih_order_info" \
              " on hi_house_id=oi_house_id"

        # 所得查询房屋数目的sql语句
        sql_total_count = "select count(distinct hi_house_id) count from ih_house_info left join ih_user_profile on hi_user_id=up_user_id " \
                          "left join ih_order_info on hi_house_id=oi_house_id"

        sql_where_li = []  # 用来保存sql语句的where条件
        sql_params = {}  # 用来保存sql查询所需的动态数据

        if area_id:
            sql_where_li.append("hi_area_id=%(area_id)s")
            sql_params["area_id"] = int(area_id)

        if start_date and end_date:
            sql_where_li.append(" a.hi_house_id not in (select oi_house_id from ih_order_info "
                                "where oi_begin_date<=%(end_date)s and oi_end_date>=%(start_date)s)")
            sql_params["start_date"] = start_date
            sql_params["end_date"] = end_date

        elif start_date:
            sql_where_li.append(" a.hi_house_id not in (select oi_house_id from ih_order_info "
                                "where oi_end_date>=%(start_date)s)")
            sql_params["start_date"] = start_date

        elif end_date:
            sql_where_li.append(" a.hi_house_id not in (select oi_house_id from ih_order_info "
                                "where oi_begin_date<=%(end_date)s)")
            sql_params["end_date"] = end_date

        if sql_where_li:
            sql += " where "
            sql += " and ".join(sql_where_li)
            sql_total_count += " where "
            sql_total_count += " and ".join(sql_where_li)

        # 有了where条件，先查询总条目数
        print sql_total_count
        print sql_params
        try:
            ret = self.db.get(sql_total_count,**sql_params)
            print("ret:%s"% ret)
        except Exception as e:
            logging.error(e)
            total_page = -1
        else:
            total_page = int(math.ceil(ret["count"] / float(constants.HOUSE_LIST_PAGE_CAPACITY)))
            if page > total_page:
                return self.write(dict(errcode=RET.OK, errmsg="OK", data=[], total_page=total_page))

        # 排序
        if "new" == sort_key:  # 按最新上传时间排序
            sql += " order by hi_ctime desc"
        elif "booking" == sort_key:  # 最受欢迎
            sql += " order by hi_order_count desc"
        elif "price-inc" == sort_key:  # 价格由低到高
            sql += " order by hi_price asc"
        elif "price-des" == sort_key:  # 价格由高到低
            sql += " order by hi_price desc"

        # 分页
        # if 1 == int(page):
        #     sql += " limit %s" % (constants.HOUSE_LIST_PAGE_CAPACITY * constants.HOUSE_LIST_PAGE_CACHE_NUM)
        # else:
        sql += " limit %s,%s" % ((page - 1) * constants.HOUSE_LIST_PAGE_CAPACITY,
                                 constants.HOUSE_LIST_PAGE_CAPACITY * constants.HOUSE_LIST_PAGE_CACHE_NUM)
        logging.debug(sql)
        try:
            ret = self.db.query(sql, **sql_params)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="查询出错"))
        data = []
        if ret:
            for l in ret:
                house = dict(
                    house_id=l["hi_house_id"],
                    title=l["hi_title"],
                    price=l["hi_price"],
                    room_count=l["hi_room_count"],
                    address=l["hi_address"],
                    order_count=l["hi_order_count"],
                    avatar=config.image_domain + l["up_avatar"] if l.get("up_avatar") else "",
                    image_url=config.image_domain + l["hi_index_image_url"] if l.get(
                        "hi_index_image_url") else ""
                )
                data.append(house)

        # 对与返回的多页面数据进行分页处理
        # 首先取出用户想要获取的page页的数据
        current_page_data = data[:constants.HOUSE_LIST_PAGE_CAPACITY]
        house_data = {}
        house_data[page] = json.dumps(
            dict(errcode=RET.OK, errmsg="OK", data=current_page_data, total_page=total_page))
        # 将多取出来的数据分页
        i = 0
        while 1:
            page_data = data[(i * constants.HOUSE_LIST_PAGE_CAPACITY):((i + 1) * constants.HOUSE_LIST_PAGE_CAPACITY)]
            if not page_data:
                break
            # 从用户传入的页码数开始缓存
            house_data[page + i] = json.dumps(dict(errcode=RET.OK, errmsg="OK", data=page_data, total_page=total_page))
            i += 1
        try:
            redis_key = "houses_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
            self.redis.hmset(redis_key, house_data)
            self.redis.expire(redis_key, constants.REDIS_INDEX_HOUSES_INFO_SECONDS)
        except Exception as e:
            logging.error(e)
        print house_data[page]
        self.write(house_data[page])