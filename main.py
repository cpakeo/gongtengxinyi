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
    url = "https://geoapi.qweather.com/v2/city/lookup?key={}&location={}".format(region, key)
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
    wind_dir = response["now"]["windDir"]
    # 降雨量（过去1小时降水量，单位mm）
    rain = response["now"].get("precip", "0") + "mm"
    # 相对湿度（百分比）
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
        hourly_resp = get(hourly_url, headers=headers, timeout=10).json()
        if hourly_resp["code"] == "200":
            rain_prob = hourly_resp["hourly"][0].get("pop", "") + "%"
    except Exception as e:
        print("获取降雨概率失败：", e)
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
        category = ""
        pm2p5 = ""

    # ===== 生活指数 获取紫外线 type=5 =====
    uv = "无"
    try:
        index_url = "https://devapi.qweather.com/v7/indices/1d?location={}&key={}&type=5".format(location_id, key)
        index_resp = get(index_url, headers=headers, timeout=10).json()
        if index_resp["code"] == "200":
            uv = index_resp["daily"][0].get("level", "无")
    except Exception as e:
        print("获取紫外线失败：", e)
        uv = "无"
    print("紫外线指数：", uv)

    # ===== 随机生活提示 proposal =====
    id = random.randint(1, 16)
    url = "https://devapi.qweather.com/v7/indices/1d?location={}&key={}&type={}".format(location_id, key, id)
    response = get(url, headers=headers).json()
    proposal = ""
    if response["code"] == "200":
        proposal += response["daily"][0]["text"]

    return weather, temp, max_temp, min_temp, wind_dir, rain, rain_prob, wet, uv, sunrise, sunset, category, pm2p5, proposal


def get_tianhang(config):
    try:
        key = config["tian_api"]
        url = "http://api.tianapi.com/caihongpi/index?key={}".format(key)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'Content-type': 'application/x-www-form-urlencoded'
        }
        response = get(url, headers=headers, timeout=10).json()
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
        try:
            year_date = ZhDate(year, r_mouth, r_day).to_datetime().date()
        except TypeError:
            print("请检查生日的日子是否在今年存在")
            os.system("pause")
            sys.exit(1)
    else:
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        year_date = date(year, birthday_month, birthday_day)
    if today > year_date:
        if birthday_year[0] == "r":
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
    """词霸每日一句"""
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
        res = r.json()
        note_en = res["content"]
        note_ch = res["note"]
        print("✅ 词霸金句获取成功")
    except Exception as e:
        print("❌ 词霸金句获取失败：", e)
    return note_ch, note_en


def get_tian_note(config):
    """天行每日一句中英金句兜底"""
    note_ch = ""
    note_en = ""
    try:
        key = config.get("tian_api", "")
        if not key:
            print("⚠️ 未配置tian_api，跳过天行金句")
            return note_ch, note_en
        url = "http://api.tianapi.com/everyday/index?key={}".format(key)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        }
        response = get(url, headers=headers, timeout=10).json()
        if response.get("code") == 200 and response.get("newslist"):
            note_ch = response["newslist"][0].get("content", "")
            note_en = response["newslist"][0].get("english", "")
            print("✅ 天行金句获取成功")
    except Exception as e:
        print("❌ 天行金句获取失败：", e)
    return note_ch, note_en


def send_message(to_user, access_token, region_name, weather, temp, wind_dir, rain, rain_prob, wet, uv,
                 note_ch, note_en, max_temp, min_temp,
                 sunrise, sunset, category, pm2p5, proposal, chp, config, yq, horoscope_data):
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    os.environ['TZ'] = 'Asia/Shanghai'
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = datetime.date(datetime(year=year, month=month, day=day))
    week = week_list[today.isoweekday() % 7]

    commemoration_data = get_commemoration_data(today, config)
    countdown_data = get_countdown_data(today, config)
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
            "wind": {
                "value": wind_dir,
                "color": color("color_wind", config)
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
        data["data"][key] = {"value": value, "color": color("color_{}".format(key), config)}
    for key, value in commemoration_data.items():
        data["data"][key] = {"value": value, "color": color("color_{}".format(key), config)}
    for key, value in countdown_data.items():
        data["data"][key] = {"value": value, "color": color("color_{}".format(key), config)}
    for key, value in birthdays.items():
        birth_day = get_birthday(value["birthday"], year, today)
        if birth_day == 0:
            birthday_data = "今天{}生日哦，祝{}生日快乐！".format(value["name"], value["name"])
        else:
            birthday_data = "距离{}的生日还有{}天".format(value["name"], birth_day)
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
        print("✅推送消息成功")
    else:
        print("推送返回：", response)


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

    accessToken = get_access_token(config)
    users = config["user"]
    region = config["region"]
    weather, temp, max_temp, min_temp, wind_dir, rain, rain_prob, wet, uv, sunrise, sunset, category, pm2p5, proposal = get_weather(region, config)

    note_ch = config["note_ch"]
    note_en = config["note_en"]
    # 只有配置文件里面两个都为空，才自动获取网络金句
    if note_ch == "" and note_en == "":
        note_ch, note_en = get_ciba()
        # 如果词霸拿不到，调用天行每日一句兜底
        if note_ch == "" or note_en == "":
            tian_ch, tian_en = get_tian_note(config)
            if note_ch == "":
                note_ch = tian_ch
            if note_en == "":
                note_en = tian_en
    print(f"📖最终中文金句：{note_ch}")
    print(f"📖最终英文金句：{note_en}")

    chp = get_tianhang(config)
    yq_data = yq(region, config)
    horoscope_data = get_horoscope(config)

    for user in users:
        send_message(user, accessToken, region, weather, temp, wind_dir, rain, rain_prob, wet, uv,
                     note_ch, note_en, max_temp, min_temp, sunrise,
                     sunset, category, pm2p5, proposal, chp, config, yq_data, horoscope_data)
    time.sleep(5)


if __name__ == "__main__":
    handler(event="", context="")
