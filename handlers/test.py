class HouseListRedisHandler(BaseHandler):
    """房屋列表信息"""
    def get(self):
        """获取房屋分页数据 使用缓存版本"""
        # 获取参数
        area_id = self.get_argument("aid", "")
        start_date = self.get_argument("sd", "")
        end_date = self.get_argument("ed", "")
        sort_key = self.get_argument("sk", "new")
        page = self.get_argument("p", "1")

        # 先读取redis缓存数据
        try:
            redis_key = "houses_%s_%s_%s_%s" % (area_id, start_date, end_date, sort_key)
            ret = self.redis.hget(redis_key, page)
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
            logging.info("hit houses list redis")
            return self.write(ret)

        # 查询数据库获取数据
        sql = "select distinct a.hi_house_id,a.hi_price,a.hi_title,a.hi_index_image_url,a.hi_room_count,a.hi_address," \
              "a.hi_order_count,b.up_avatar  from ih_house_info a inner join ih_user_profile b " \
              "on a.hi_user_id=b.up_user_id left join ih_order_info c on a.hi_house_id=c.oi_house_id"
        sql_total_page = "select count(distinct a.hi_house_id) as counts from ih_house_info a inner join " \
                         "ih_user_profile b on a.hi_user_id=b.up_user_id left join ih_order_info c " \
                         "on a.hi_house_id=c.oi_house_id"

        # 存放可能的筛选条件
        sql_where_li = []

        # 存放动态绑定需要的参数值
        sql_params = {}

        if area_id:
            sql_where_li.append("hi_area_id=%(area_id)s")
            sql_params["area_id"] = int(area_id)

        # 早先版本的日期筛选条件有错误，此处注释的为错误的版本
        # if start_date and end_date:
        #     sql_where.append("(oi_start_date is null or oi_end_date is null or c.oi_start_date>%(end_date)s "
        #                      "or c.oi_end_date < %(start_date)s)")
        #     sql_value["start_date"] = start_date
        #     sql_value["end_date"] = end_date
        # elif start_date:
        #     sql_where.append("(oi_start_date is null or oi_end_date is null or c.oi_end_date < %(start_date)s)")
        #     sql_value["start_date"] = start_date
        # elif end_date:
        #     sql_where.append("(oi_start_date is null or oi_end_date is null or c.oi_start_date>%(end_date)s)")
        #     sql_value["end_date"] = end_date

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
            sql_total_page += " where "
            sql_total_page += " and ".join(sql_where_li)

        # 查询总页数
        try:
            logging.debug(sql_total_page)
            ret = self.db.get(sql_total_page, **sql_params)
        except Exception as e:
            logging.error(e)
            ret = None
            total_page = -1
        else:
            # 总数为0代表无数据
            if 0 == ret["counts"]:
                return self.write({"errno": RET.OK, "errmsg": "OK", "total_page": 0, "data": []})

            page = int(page)
            total_page = int(math.ceil(float(ret["counts"]) / constants.HOUSE_LIST_PAGE_CAPACITY))
            # 如果用户要查询的页数大于总页数，直接返回
            if page > total_page:
                return self.write({"errno": RET.OK, "errmsg": "OK", "total_page": total_page, "data": []})

        sql += " order by "
        if "booking" == sort_key:
            sql += "a.hi_order_count desc"
        elif "price-inc" == sort_key:
            sql += "a.hi_price"
        elif "price-des" == sort_key:
            sql += "a.hi_price desc"
        else:
            sql += "a.hi_ctime desc"

        if 1 == page:
            sql += (" limit %s" % (constants.HOUSE_LIST_PAGE_CAPACITY * constants.HOUSE_LIST_REDIS_CACHED_PAGE))
        else:
            sql += (" limit %s,%s" % ((page-1) * constants.HOUSE_LIST_PAGE_CAPACITY,
                                      constants.HOUSE_LIST_PAGE_CAPACITY * constants.HOUSE_LIST_REDIS_CACHED_PAGE))

        try:
            logging.debug(sql)
            ret = self.db.query(sql, **sql_params)
        except Exception as e:
            logging.error(e)
            return self.write({"errno": RET.DBERR, "errmsg": "get data error"})

        if not ret:
            return self.write({"errno": RET.OK, "errmsg": "OK", "total_page": total_page, "data": []})
        houses = []
        for l in ret:
            house = {
                "house_id": l["hi_house_id"],
                "title": l["hi_title"],
                "price": l["hi_price"],
                "room_count": l["hi_room_count"],
                "order_count": l["hi_order_count"],
                "address": l["hi_address"],
                "img_url": image_url_prefix + l["hi_index_image_url"] if l["hi_index_image_url"] else "",
                "avatar_url": image_url_prefix + l["up_avatar"] if l["up_avatar"] else ""
            }
            houses.append(house)

        redis_data = {}
        # 切片拿到的每页数据
        i = 0
        while True:
            page_data = houses[(i*constants.HOUSE_LIST_PAGE_CAPACITY):((i+1)*constants.HOUSE_LIST_PAGE_CAPACITY)]
            if not page_data:
                break
            redis_data[str(page+i)] = json.dumps({"errno": RET.OK, "errmsg": "OK", "total_page": total_page,
                                                  "data": page_data})
            i += 1

        redis_key = "houses_%s_%s_%s_%s" % (area_id, start_date, end_date, sort_key)

        # 设置redis的hash数据
        try:
            self.redis.hmset(redis_key, redis_data)
        except Exception as e:
            logging.error(e)
            return

        # 设置redis数据的有效期
        try:
            self.redis.expire(redis_key, constants.HOUSE_LIST_REDIS_EXPIRE_SECOND)
        except Exception as e:
            logging.error(e)
            self.redis.delete(redis_key)

        self.write(redis_data[str(page)])