# coding:utf-8

import logging
import datetime
import config
from handlers.BaseHandler import BaseHandler
from utils.commons import required_login
from utils.response_code import RET


class OrderHandler(BaseHandler):
    """订单"""
    @required_login
    def post(self):
        """提交订单"""
        user_id = self.session.data["up_user_id"]
        house_id = self.json_dict.get("house_id")
        start_date = self.json_dict.get("start_date")
        end_date = self.json_dict.get("end_date")
        # 参数检查
        if not all((house_id, start_date, end_date)):
            return self.write({"errcode":RET.PARAMERR, "errmsg":"params error"})
        # 查询房屋是否存在
        try:
            house = self.db.get("select hi_price,hi_user_id from ih_house_info where hi_house_id=%s", house_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode":RET.DBERR, "errmsg":"get house error"})
        if not house:
            return self.write({"errcode":RET.NODATA, "errmsg":"no data"})
        # 预订的房屋是否是房东自己的
        if user_id == house["hi_user_id"]:
            return self.write({"errcode":RET.ROLEERR, "errmsg":"user is forbidden"})
        # 判断预定天数
        days = (datetime.datetime.strptime(end_date, "%Y-%m-%d") - datetime.datetime.strptime(start_date, "%Y-%m-%d")).days + 1
        if days<=0:
            return self.write({"errcode":RET.PARAMERR, "errmsg":"date params error"})
        # 确保用户预订的时间内，房屋没有被别人下单
        try:
            ret = self.db.get("select count(*) counts from ih_order_info where oi_house_id=%(house_id)s "
                              "and oi_begin_date<%(end_date)s and oi_end_date>%(start_date)s",
                              house_id=house_id, end_date=end_date, start_date=start_date)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode":RET.DBERR, "errmsg":"get date error"})
        if ret["counts"] > 0:
            return self.write({"errcode":RET.DATAERR, "errmsg":"serve date error"})
        amount = days * house["hi_price"]
        try:
            # 生成订单,并更新订单计数
            self.db.execute("insert into ih_order_info(oi_user_id,oi_house_id,oi_begin_date,"
                            "oi_end_date,oi_days,oi_house_price,oi_amount)"
                            " values(%(user_id)s,%(house_id)s,%(begin_date)s,%(end_date)s,%(days)s,%(price)s,%(amount)s);"
                            "update ih_house_info set hi_order_count=hi_order_count+1 where hi_house_id=%(house_id)s;",
                            user_id=user_id, house_id=house_id, begin_date=start_date, end_date=end_date, days=days, price=house["hi_price"], amount=amount)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode":RET.DBERR, "errmsg":"save data error"})
        self.write({"errcode":RET.OK, "errmsg":"OK"})


class MyOrderHandler(BaseHandler):
    """未完成订单"""
    @required_login
    def get(self):
        user_mode = self.get_argument('role','')
        user_id = self.session.data["up_user_id"]
        print user_mode
        # 作为房客查询下的订单
        if user_mode == "custom":
            sql = "select oi_order_id,hi_title,hi_index_image_url,oi_begin_date,oi_end_date,oi_ctime,oi_days,oi_amount," \
                  "oi_status,oi_comment from ih_order_info left join ih_house_info on oi_house_id = hi_house_id " \
                  "where oi_user_id = %s order by oi_ctime desc;"
        # 作为房东查询被下的订单
        elif user_mode == "landlord":
            sql = "select oi_order_id,hi_title,hi_index_image_url,oi_begin_date,oi_end_date,oi_ctime,oi_days,oi_amount," \
                  "oi_status,oi_comment from ih_order_info left join ih_house_info on oi_house_id = hi_house_id " \
                  "where hi_user_id = %s order by oi_ctime desc;"
        else:
            return self.write({"errcode":RET.PARAMERR, "errmsg":"user mode err"})
        try:
            orders_data = self.db.query(sql, user_id)
        except Exception as e:
            logging.error(e)
        if not orders_data:
            return self.write({"errcode": RET.NODATA, "errmsg": "no orders"})
        print ("orders_data:%s"%orders_data)
        orders = []
        for l in orders_data:
            order={
                "order_id": l["oi_order_id"],
                "title": l["hi_title"],
                "img_url": config.image_domain + l["hi_index_image_url"] if l["hi_index_image_url"] else "",
                "start_date": l["oi_begin_date"].strftime("%Y-%m-%d"),
                "end_date": l["oi_end_date"].strftime("%Y-%m-%d"),
                "ctime": l["oi_ctime"].strftime("%Y-%m-%d"),
                "days": l["oi_days"],
                "amount": l["oi_amount"],
                "status": l["oi_status"],
                "comment": l["oi_comment"] if l["oi_comment"] else ""
            }
            orders.append(order)
        print ("orders:%s"%orders)
        return self.write({"errcode": RET.OK, "errmsg": "OK", "orders":orders})


class AcceptOrderHandler(BaseHandler):
    """提交订单"""
    @required_login
    def post(self):
        print self.json_dict
        user_id = self.session.data["up_user_id"]
        order_id = self.json_dict.get('order_id')
        if not order_id:
            return self.write({"errcode": RET.PARAMERR, "errmsg": "order err"})
        user_id = self.session.data["up_user_id"]
        # 确认登陆用户是否为房主
        sql = "select hi_user_id  from ih_order_info left join ih_house_info on oi_house_id = hi_house_id where oi_order_id=%s;"
        try:
            landlord =  self.db.get(sql, order_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DATAERR, "errmsg": "database err"})
        if not landlord:
            return self.write({"errcode": RET.NODATA, "errmsg": "no data"})
        print landlord
        print user_id
        if landlord['hi_user_id'] != user_id:
            return self.write({"errcode": RET.ROLEERR, "errmsg": "role err"})
        # 确认成功，更改订单状态,跳过支付功能直接设置成待评价
        sql = "update ih_order_info set oi_status = 2 where oi_order_id=%s and oi_status=0"
        try:
            self.db.execute(sql, order_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DATAERR, "errmsg": "database err"})
        self.write({"errcode": RET.OK, "errmsg": "ok"})


class CommentOrderHandler(BaseHandler):
    """评论"""
    @required_login
    def post(self):
        print self.json_dict
        user_id = self.session.data["up_user_id"]
        order_id = self.json_dict.get('order_id')
        comment = self.json_dict.get('comment')
        if not all((order_id, comment)):
            return self.write({"errcode": RET.PARAMERR, "errmsg": "order err"})
        pass
        # 确认登陆用户是否为订单主人
        sql = "select * from ih_order_info  where oi_order_id=%s and oi_user_id=%s;"
        try:
            result = self.db.get(sql, order_id, user_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DATAERR, "errmsg": "database err"})
        if not result:
            return self.write({"errcode": RET.NODATA, "errmsg": "role err"})
            # 确认订单状态是否待待评论，确认完成更新评论
        sql = "update ih_order_info set oi_status=4,oi_comment=%s where oi_order_id=%s and oi_status=3"
        try:
            self.db.execute(sql, comment, order_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DATAERR, "errmsg": "database err"})
        self.write({"errcode": RET.OK, "errmsg": "ok"})


class RejectOrderHandler(BaseHandler):
    """拒单"""
    @required_login
    def post(self):
        print self.json_dict
        user_id = self.session.data["up_user_id"]
        order_id = self.json_dict.get('order_id')
        reject_reason = self.json_dict.get('reject_reason')
        if not all((order_id,reject_reason)):
            return self.write({"errcode": RET.PARAMERR, "errmsg": "order err"})
        pass
    # 确认登陆用户是否为房主
        sql = "select hi_user_id  from ih_order_info left join ih_house_info on oi_house_id = hi_house_id where oi_order_id=%s;"
        try:
            landlord =  self.db.get(sql, order_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DATAERR, "errmsg": "database err"})
        if not landlord:
            return self.write({"errcode": RET.NODATA, "errmsg": "no data"})
        print landlord
        print user_id
        if landlord['hi_user_id'] != user_id:
            return self.write({"errcode": RET.ROLEERR, "errmsg": "role err"})
    # 确认订单状态是否待接单,更改订单状态并更新评论
        sql = "update ih_order_info set oi_status=6,oi_comment=%s where oi_order_id=%s and oi_status=0"
        try:
            self.db.execute(sql, reject_reason, order_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DATAERR, "errmsg": "database err"})
        self.write({"errcode": RET.OK, "errmsg": "ok"})

