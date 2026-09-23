import random
import time
from time import localtime
# from time import tzset
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os


def get_horoscope(config_data):
    # 获取所有星座数据
    horoscope_data = {}
    for k, v in config_data.items():
        if k[0:9] == "horoscope":
            try:
                key = config_data["tian_api"]
                url = "http://api.tianapi.com/star/index?key={}&astro={}".format(key, v)
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                    'Content-type': 'application/x-www-form-urlencoded'
                }
                response = get(url, headers=headers).json()
                if response["code"] == 200:
                    horoscope = response["newslist"][-1]["content"]
                    horoscope = horoscope.split("。")[0]
                else:
                    horoscope = ""
            except KeyError:
                horoscope = ""
            horoscope_data[k] = horoscope
    return horoscope_data


def yq(region, config_data):
    key = config_data["weather_key"]
    url = "https://geoapi.qweather.com/v2/city/lookup?key={}&location={}".format(key, region)
    r = get(url).json()
    if r["code"] == "200":
        city = r["location"][0]["adm2"]
        if region in ["台北", "高雄", "台中", "台湾"]:
            city = "台湾"
    else:
        city = ""
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Mobile Safari/537.36',
    }
    response = get('https://covid.myquark.cn/quark/covid/data?city={}'.format(city), headers=headers).json()
    if city in ["北京", "上海", "天津", "重庆", "香港", "澳门", "台湾"]:
        city_data = response["provinceData"]
    else:
        city_data = response["cityData"]
    try:
        sure_new_loc = "昨日新增：{}".format(city_data["sure_new_loc"])
        sure_new_hid = "昨日无症状：{}".format(city_data["sure_new_hid"])
        present = "现有确诊：{}".format(city_data["present"])
        danger = "中/高风险区：{}/{}".format(city_data["danger"]["1"], city_data["danger"]["2"])
        statistics_time = response["time"]
        yq_data = "{}疫情数据\n{}\n{}\n{}\n{}\n{}".format(city, sure_new_loc, sure_new_hid, present, danger, statistics_time)
    except TypeError:
        yq_data = ""
    return yq_data


def get_commemoration_day(today, commemoration_day):
    # 获取纪念日的日期格式
    commemoration_year = int(commemoration_day.split("-")[0])
    commemoration_month = int(commemoration_day.split("-")[1])
    commemoration_day = int(commemoration_day.split("-")[2])
    commemoration_date = date(commemoration_year, commemoration_month, commemoration_day)
    # 获取纪念日的日期差
    commemoration_days = str(today.__sub__(commemoration_date)).split(" ")[0]
    return commemoration_days


def get_commemoration_data(today, config_data):
    # 获取所有纪念日数据
    commemoration_days = {}
    for k, v in config_data.items():
        if k[0:13] == "commemoration":
            commemoration_days[k] = get_commemoration_day(today, v)
    return commemoration_days


def get_countdown_data(today, config_data):
    # 获取所有倒计时数据
    countdown_data = {}
    for k, v in config_data.items():
        if k[0:9] == "countdown":
            countdown_year = int(v.split("-")[0])
            countdown_month = int(v.split("-")[1])
            countdown_day = int(v.split("-")[2])
            countdown_date = date(countdown_year, countdown_month, countdown_day)
            if today == countdown_date:
                countdown_data[k] = 0
            else:
                countdown_data[k] = str(countdown_date.__sub__(today)).split(" ")[0]
    return countdown_data


def color(name, config):
    # 获取字体颜色，如没设置返回随机颜色
    try:
        if config[name] == "":
            color = get_color()
        else:
            color = config[name]
        return color
    except KeyError:
        color = get_color()
        return color


def get_color():
    # 获取随机颜色
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)


def get_access_token(config):
    # appId
    app_id = config["app_id"]
    # appSecret
    app_secret = config["app_secret"]
    post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
                .format(app_id, app_secret))
    try:
        access_token = get(post_url).json()['access_token']
    except KeyError:
        print("获取access_token失败，请检查app_id和app_secret是否正确")
        os.system("pause")
        sys.exit(1)
    return access_token


def get_weather(region, config):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config["weather_key"]
    region_url = "https://geoapi.qweather.com/v2/city/lookup?location={}&key={}".format(region, key)
    response = get(region_url, headers=headers).json()
    if response["code"] == "404":
        print("推送消息失败，请检查地区名是否有误！")
        os.system("pause")
        sys.exit(1)
    elif response["code"] == "401":
        print("推送消息失败，请检查和风天气key是否正确！")
        os.system("pause")
        sys.exit(1)
    else:
        # 获取地区的location--id
        location_id = response["location"][0]["id"]
    # ===== 实时天气 now =====
    weather_url = "https://devapi.qweather.com/v7/weather/now?location={}&key={}".format(location_id, key)
    response = get(weather_url, headers=headers).json()
    # 天气
    weather = response["now"]["text"]
    # 当前温度
    temp = response["now"]["temp"] + u"\N{DEGREE SIGN}" + "C"
    # 风向
    wind = response["now"]["windDir"]
    # 【新增】风力等级
    windScale = response["now"]["windScale"]
    # 【新增】降雨量（过去1小时降水量，单位mm）
    rain = response["now"].get("precip", "0") + "mm"
    # 【新增】相对湿度（百分比）
    wet = response["now"].get("humidity", "") + "%"
    # ===== 逐日预报 3d =====
    url = "https://devapi.qweather.com/v7/weather/3d?location={}&key={}".format(location_id, key)
    response = get(url, headers=headers).json()
    print("3d天气接口返回code：", response["code"])
    # 最高气温
    max_temp = response["daily"][0]["tempMax"] + u"\N{DEGREE SIGN}" + "C"
    # 最低气温
    min_temp = response["daily"][0]["tempMin"] + u"\N{DEGREE SIGN}" + "C"
    # 日出时间
    sunrise = response["daily"][0]["sunrise"]
    # 日落时间
    sunset = response["daily"][0]["sunset"]
    # ===== 逐小时预报 24h（获取降雨概率） =====
    rain_prob = ""
    try:
        hourly_url = "https://devapi.qweather.com/v7/weather/24h?location={}&key={}".format(location_id, key)
        hourly_resp = get(hourly_url, headers=headers).json()
        if hourly_resp["code"] == "200":
            rain_prob = hourly_resp["hourly"][0].get("pop", "") + "%"
    except Exception:
        rain_prob = ""
    # ===== 空气质量 =====
    url = "https://devapi.qweather.com/v7/air/now?location={}&key={}".format(location_id, key)
    response = get(url, headers=headers).json()
    if response["code"] == "200":
        # 空气质量
        category = response["now"]["category"]
        # pm2.5
        pm2p5 = response["now"]["pm2p5"]
    else:
        # 国外城市获取不到数据
        category = ""
        pm2p5 = ""
    # ===== 生活指数 【这里获取紫外线 type=5 紫外线指数】=====
    uv = "无"
    try:
        index_url = "https://devapi.qweather.com/v7/indices/1d?location={}&key={}&type=5".format(location_id, key)
        index_resp = get(index_url, headers=headers).json()
        if index_resp["code"] == "200":
            uv = index_resp["daily"][0].get("level","无")
    except Exception:
        uv = "无"
    print("紫外线指数：", uv)
    # ===== 随机生活提示（原来的proposal） =====
    id = random.randint(1, 16)
    url = "https://devapi.qweather.com/v7/indices/1d?location={}&key={}&type={}".format(location_id, key, id)
    response = get(url, headers=headers).json()
    proposal = ""
    if response["code"] == "200":
        proposal += response["daily"][0]["text"]

    # 返回增加 windScale（风力）
    return weather, temp, max_temp, min_temp, wind_dir, windScale, rain, rain_prob, wet, uv, sunrise, sunset, category, pm2p5, proposal


def get_tianhang(config):
    try:
        key = config["tian_api"]
        url = "http://api.tianapi.com/caihongpi/index?key={}".format(key)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'Content-type': 'application/x-www-form-urlencoded'
        }
        response = get(url, headers=headers).json()
        if response["code"] == 200:
            chp = response["newslist"][0]["content"]
        else:
            chp = ""
    except KeyError:
        chp = ""
    return chp


def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    # 判断是否为农历生日
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        # 获取农历生日的生日
        try:
            year_date = ZhDate(year, r_mouth, r_day).to_datetime().date()
        except TypeError:
            print("请检查生日的日子是否在今年存在")
            os.system("pause")
            sys.exit(1)
    else:
        # 获取国历生日的今年对应月和日
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        # 今年生日
        year_date = date(year, birthday_month, birthday_day)
    # 计算生日年份，如果还没过，按当年减，如果过了需要+1
    if today > year_date:
        if birthday_year[0] == "r":
            # 获取农历明年生日的月和日
            r_last_birthday = ZhDate((year + 1), r_mouth, r_day).to_datetime().date()
            birth_date = date((year + 1), r_last_birthday.month, r_last_birthday.day)
        else:
            birth_date = date((year + 1), birthday_month, birthday_day)
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    elif today == year_date:
        birth_day = 0
    else:
        birth_date = year_date
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    return birth_day


def get_ciba():
    """词霸每日一句，失败则返回空"""
    note_ch = ""
    note_en = ""
    try:
        url = "http://open.iciba.com/dsapi/"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        }
        r = get(url, headers=headers, timeout=10)
        res_data = r.json()
        note_en = res_data["content"]
        note_ch = res_data["note"]
    except Exception as e:
        print("词霸接口获取失败：", e)
    return note_ch, note_en


def get_tian_note(config):
    note_ch = ""
    note_en = ""
    try:
        key = config["tian_api"]
        import http.client
        import urllib.parse
        import json
        conn = http.client.HTTPSConnection('apis.tianapi.com')
        params = urllib.parse.urlencode({'key': key})
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        conn.request('POST','/everyday/index', params, headers)
        tianapi = conn.getresponse()
        result = tianapi.read()
        data = result.decode('utf-8')
        dict_data = json.loads(data)
        print("【天行每日金句POST返回】", dict_data)
        conn.close()
        if dict_data.get("code") == 200:
            res = dict_data.get("result", {})
            note_en = res.get("content", "")
            note_ch = res.get("note", "")
    except Exception as e:
        print("天行金句POST调用异常：", e)
    # 第一步兜底：调用词霸
    if not note_ch or not note_en:
        print("天行金句无数据，启用词霸兜底")
        note_ch, note_en = get_ciba()
    # ✅终极兜底：词霸也超时/失败，使用内置备用金句列表，保证绝不空白
    backup_list = [
        ("保持热爱，奔赴山海", "Keep loving, keep going."),
        ("凡心所向，素履以往", "Follow your heart, and you will find your way."),
        ("生活明朗，万物可爱", "Life is bright and everything is lovely."),
        ("慢慢来，好戏都在烟火里", "Take your time, good things are in ordinary life."),
        ("愿你历尽千帆，归来仍是少年", "May you return as a youth after all your journeys.")
    ]
    if not note_ch or not note_en:
        import random
        print("⚠️词霸也失效，启用本地内置金句！")
        note_ch, note_en = random.choice(backup_list)
    return note_ch, note_en


def send_message(to_user, access_token, region_name, weather, temp, max_temp, min_temp, wind_dir, windScale, rain, rain_prob, wet, uv,
                 note_ch, note_en, sunrise, sunset, category, pm2p5, proposal, chp, config, yq, horoscope_data):
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    os.environ['TZ'] = 'Asia/Shanghai'
    # tzset()
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = datetime.date(datetime(year=year, month=month, day=day))
    week = week_list[today.isoweekday() % 7]
    # 获取所有纪念日数据
    commemoration_data = get_commemoration_data(today, config)
    # 获取所有倒计时数据
    countdown_data = get_countdown_data(today, config)
    # 获取所有生日数据
    birthdays = {}
    for k, v in config.items():
        if k[0:5] == "birth":
            birthdays[k] = v
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {
                "value": "{} {}".format(today, week),
                "color": color("color_date", config)
            },
            "region": {
                "value": region_name,
                "color": color("color_region", config)
            },
            "weather": {
                "value": weather,
                "color": color("color_weather", config)
            },
            "temp": {
                "value": temp,
                "color": color("color_temp", config)
            },
            "wind_dir": {
                "value": wind_dir,
                "color": color("color_wind_dir", config)
            },
            "wind_scale": {
                "value": f"{windScale}级" if windScale else "",
                "color": color("color_wind_scale", config)
            },
            "rain": {
                "value": rain,
                "color": color("color_weather", config)
            },
            "rain_prob": {
                "value": rain_prob,
                "color": color("color_weather", config)
            },
            "wet": {
                "value": wet,
                "color": color("color_weather", config)
            },
            "uv": {
                "value": uv,
                "color": color("color_weather", config)
            },
            "note_en": {
                "value": note_en,
                "color": color("color_note_en", config)
            },
            "note_ch": {
                "value": note_ch,
                "color": color("color_note_ch", config)
            },
            "max_temp": {
                "value": max_temp,
                "color": color("color_max_temp", config)
            },
            "min_temp": {
                "value": min_temp,
                "color": color("color_min_temp", config)
            },
            "sunrise": {
                "value": sunrise,
                "color": color("color_sunrise", config)
            },
            "sunset": {
                "value": sunset,
                "color": color("color_sunset", config)
            },
            "category": {
                "value": category,
                "color": color("color_category", config)
            },
            "pm2p5": {
                "value": pm2p5,
                "color": color("color_pm2p5", config)
            },
            "proposal": {
                "value": proposal,
                "color": color("color_proposal", config)
            },
            "chp": {
                "value": chp,
                "color": color("color_chp", config)
            },
            "yq": {
                "value": yq,
                "color": color("color_yq", config)
            },
        }
    }
    for key, value in horoscope_data.items():
        # 将星座数据插入data
        data["data"][key] = {"value": value, "color": color("color_{}".format(key), config)}
    for key, value in commemoration_data.items():
        # 将纪念日数据插入data
        data["data"][key] = {"value": value, "color": color("color_{}".format(key), config)}
    for key, value in countdown_data.items():
        # 将倒计时数据插入data
        data["data"][key] = {"value": value, "color": color("color_{}".format(key), config)}
    for key, value in birthdays.items():
        # 获取距离下次生日的时间
        birth_day = get_birthday(value["birthday"], year, today)
        if birth_day == 0:
            birthday_data = "今天{}生日哦，祝{}生日快乐！".format(value["name"], value["name"])
        else:
            birthday_data = "距离{}的生日还有{}天".format(value["name"], birth_day)
        # 将生日数据插入data
        data["data"][key] = {"value": birthday_data, "color": color("color_{}".format(key), config)}
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    response = post(url, headers=headers, json=data).json()
    if response["errcode"] == 40037:
        print("推送消息失败，请检查模板id是否正确")
        os.system("pause")
        sys.exit(1)
    elif response["errcode"] == 40036:
        print("推送消息失败，请检查模板id是否为空")
        os.system("pause")
        sys.exit(1)
    elif response["errcode"] == 40003:
        print("推送消息失败，请检查微信号是否正确")
        os.system("pause")
        sys.exit(1)
    elif response["errcode"] == 43004:
        print("推送消息失败，用户取消关注公众号")
        os.system("pause")
        sys.exit(1)
    elif response["errcode"] == 0:
        print("推送消息成功")
    else:
        print(response)


def handler(event, context):
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except FileNotFoundError:
        print("推送消息失败，请检查config.txt文件是否与程序位于同一路径")
        os.system("pause")
        sys.exit(1)
    except SyntaxError:
        print("推送消息失败，请检查配置文件格式是否正确")
        os.system("pause")
        sys.exit(1)
    # 获取accessToken
    accessToken = get_access_token(config)
    # 接收的用户
    users = config["user"]
    # 传入地区获取天气信息（返回增加 windScale）
    region = config["region"]
    weather, temp, max_temp, min_temp, wind_dir, windScale, rain, rain_prob, wet, uv, sunrise, sunset, category, pm2p5, proposal = get_weather(region, config)
    note_ch = config["note_ch"]
    note_en = config["note_en"]
    if note_ch == "" and note_en == "":
        # 先试词霸
        note_ch, note_en = get_ciba()
        # 词霸失败则用天行每日一句兜底
        if note_ch == "" or note_en == "":
            tian_ch, tian_en = get_tian_note(config)
            if note_ch == "":
                note_ch = tian_ch
            if note_en == "":
                note_en = tian_en
    chp = get_tianhang(config)
    # 获取疫情数据
    yq_data = yq(region, config)
    # 获取星座数据
    horoscope_data = get_horoscope(config)
    # 公众号推送消息
    for user in users:
        send_message(user, accessToken, region, weather, temp, max_temp, min_temp, wind_dir, windScale, rain, rain_prob, wet, uv,
                     note_ch, note_en, sunrise,
                     sunset, category, pm2p5, proposal, chp, config, yq_data, horoscope_data)
    time.sleep(5)


if __name__ == "__main__":
    handler(event="", context="")
