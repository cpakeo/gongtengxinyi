import random
import time
from time import localtime
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os
# ============================================================
# 和风天气统一请求函数
# ============================================================
def qweather_get(path, config, params=None, timeout=15):
    api_host = config.get("qweather_api_host", "").strip()
    api_key = config.get("weather_key", "").strip()
    if not api_host:
        print("❌ 没有配置 qweather_api_host")
        print("请在 config.txt 中增加：")
        print('"qweather_api_host": "你的API Host"')
        sys.exit(1)
    if not api_host.startswith("http://") and not api_host.startswith("https://"):
        api_host = "https://" + api_host
    api_host = api_host.rstrip("/")
    url = api_host + path
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json"
    }
    # API KEY 使用请求参数方式
    if params is None:
        params = {}
    params["key"] = api_key
    try:
        response = get(
            url,
            headers=headers,
            params=params,
            timeout=timeout
        )
        print("和风天气请求：", path)
        print("HTTP 状态码：", response.status_code)
        print("Content-Type：", response.headers.get("Content-Type"))
        print(
            "接口返回：",
            repr(response.text[:2000])
        )
        if response.status_code != 200:
            print(
                "❌ 和风天气 HTTP 请求失败"
            )
            print(
                "状态码：",
                response.status_code
            )
            print(
                "URL：",
                url
            )
            sys.exit(1)
        if not response.text.strip():
            print(
                "❌ 和风天气接口返回为空"
            )
            sys.exit(1)
        try:
            result = response.json()
        except Exception as e:
            print(
                "❌ 和风天气返回内容不是 JSON"
            )
            print(
                "JSON解析错误：",
                e
            )
            print(
                "原始返回：",
                repr(response.text[:5000])
            )
            sys.exit(1)
        return result
    except Exception as e:
        print(
            "❌ 和风天气请求异常：",
            e
        )
        sys.exit(1)
# ============================================================
# 星座运势
# ============================================================
def get_horoscope(config_data):
    horoscope_data = {}
    for k, v in config_data.items():
        if k.startswith("horoscope"):
            try:
                key = config_data["tian_api"]
                url = (
                    "https://apis.tianapi.com/star/index"
                    "?key={}&astro={}"
                ).format(
                    key,
                    v
                )
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/150.0.0.0 Safari/537.36"
                    )
                }
                r = get(
                    url,
                    headers=headers,
                    timeout=15
                )
                print(
                    "星座接口 HTTP 状态码：",
                    r.status_code
                )
                print(
                    "星座接口原始返回：",
                    repr(r.text[:1000])
                )
                response = r.json()
                if response.get("code") == 200:
                    result = response.get(
                        "result",
                        {}
                    )
                    if (
                        result
                        and result.get("list")
                        and len(result["list"]) > 0
                    ):
                        horoscope = result["list"][0].get(
                            "content",
                            "暂无星座运势"
                        )
                    else:
                        horoscope = "暂无星座运势"
                else:
                    horoscope = "暂无星座运势"
            except Exception as e:
                print(
                    "星座获取异常 {}：".format(k),
                    e
                )
                horoscope = "暂无星座运势"
            horoscope_data[k] = horoscope
    return horoscope_data
# ============================================================
# 疫情数据
# ============================================================
def yq(region, config_data):
    try:
        response = qweather_get(
            "/geo/v2/city/lookup",
            config_data,
            {
                "location": region
            }
        )
        city = ""
        if response.get("code") == "200":
            if response.get("location"):
                city = response["location"][0]["adm2"]
        if not city:
            return ""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 "
                "Build/MRA58N) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/150.0.0.0 "
                "Mobile Safari/537.36"
            )
        }
        response = get(
            "https://covid.myquark.cn/quark/covid/data"
            "?city={}".format(city),
            headers=headers,
            timeout=15
        ).json()
        if city in [
            "北京",
            "上海",
            "天津",
            "重庆",
            "香港",
            "澳门",
            "台湾"
        ]:
            city_data = response["provinceData"]
        else:
            city_data = response["cityData"]
        sure_new_loc = "昨日新增：{}".format(
            city_data["sure_new_loc"]
        )
        sure_new_hid = "昨日无症状：{}".format(
            city_data["sure_new_hid"]
        )
        present = "现有确诊：{}".format(
            city_data["present"]
        )
        danger = "中/高风险区：{}/{}".format(
            city_data["danger"]["1"],
            city_data["danger"]["2"]
        )
        statistics_time = response["time"]
        yq_data = "{}疫情数据\n{}\n{}\n{}\n{}\n{}".format(
            city,
            sure_new_loc,
            sure_new_hid,
            present,
            danger,
            statistics_time
        )
    except Exception as e:
        print(
            "疫情数据获取失败：",
            e
        )
        yq_data = ""
    return yq_data
# ============================================================
# 纪念日
# ============================================================
def get_commemoration_day(
    today,
    commemoration_day
):
    commemoration_year = int(
        commemoration_day.split("-")[0]
    )
    commemoration_month = int(
        commemoration_day.split("-")[1]
    )
    commemoration_day = int(
        commemoration_day.split("-")[2]
    )
    commemoration_date = date(
        commemoration_year,
        commemoration_month,
        commemoration_day
    )
    commemoration_days = str(
        today.__sub__(
            commemoration_date
        )
    ).split(" ")[0]
    return commemoration_days
def get_commemoration_data(
    today,
    config_data
):
    commemoration_days = {}
    for k, v in config_data.items():
        if k.startswith("commemoration"):
            commemoration_days[k] = (
                get_commemoration_day(
                    today,
                    v
                )
            )
    return commemoration_days
# ============================================================
# 倒计时
# ============================================================
def get_countdown_data(
    today,
    config_data
):
    countdown_data = {}
    for k, v in config_data.items():
        if k.startswith("countdown"):
            countdown_year = int(
                v.split("-")[0]
            )
            countdown_month = int(
                v.split("-")[1]
            )
            countdown_day = int(
                v.split("-")[2]
            )
            countdown_date = date(
                countdown_year,
                countdown_month,
                countdown_day
            )
            if today == countdown_date:
                countdown_data[k] = 0
            else:
                countdown_data[k] = str(
                    countdown_date.__sub__(
                        today
                    )
                ).split(" ")[0]
    return countdown_data
# ============================================================
# 颜色
# ============================================================
def color(name, config):
    try:
        if config[name] == "":
            return get_color()
        else:
            return config[name]
    except KeyError:
        return get_color()
def get_color():
    get_colors = lambda n: list(
        map(
            lambda i:
            "#" + "%06x" % random.randint(
                0,
                0xFFFFFF
            ),
            range(n)
        )
    )
    color_list = get_colors(100)
    return random.choice(
        color_list
    )
# ============================================================
# 微信 Access Token
# ============================================================
def get_access_token(config):
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    post_url = (
        "https://api.weixin.qq.com/cgi-bin/token"
        "?grant_type=client_credential"
        "&appid={}"
        "&secret={}"
    ).format(
        app_id,
        app_secret
    )
    try:
        response = get(
            post_url,
            timeout=15
        ).json()
        print(
            "微信 Access Token 接口返回：",
            response
        )
        if "access_token" not in response:
            print(
                "❌ 获取 Access Token 失败"
            )
            print(
                "微信返回：",
                response
            )
            sys.exit(1)
        access_token = response[
            "access_token"
        ]
        print(
            "✅ Access Token 获取成功"
        )
    except Exception as e:
        print(
            "❌ 获取 Access Token 失败：",
            e
        )
        sys.exit(1)
    return access_token
# ============================================================
# 天气
# ============================================================
def get_weather(
    region,
    config
):
    print("====================================")
    print("正在获取天气数据……")
    print("正在查询地区：", region)
    print("====================================")
    # ========================================================
    # 1. 地区查询
    # ========================================================
    response = qweather_get(
        "/geo/v2/city/lookup",
        config,
        {
            "location": region
        }
    )
    print(
        "和风天气地区查询结果：",
        response
    )
    if response.get("code") != "200":
        print(
            "❌ 地区查询失败：",
            response
        )
        sys.exit(1)
    if not response.get("location"):
        print(
            "❌ 和风天气没有返回地区"
        )
        sys.exit(1)
    location = response["location"][0]
    location_id = location["id"]
    latitude = location["lat"]
    longitude = location["lon"]
    print(
        "✅ 地区查询成功"
    )
    print(
        "地区：",
        region
    )
    print(
        "Location ID：",
        location_id
    )
    print(
        "经纬度：",
        latitude,
        longitude
    )
    # ========================================================
    # 2. 当前天气
    # ========================================================
    response = qweather_get(
        "/v7/weather/now",
        config,
        {
            "location": location_id
        }
    )
    if response.get("code") != "200":
        print(
            "❌ 当前天气获取失败：",
            response
        )
        sys.exit(1)
    now = response["now"]
    weather = now.get(
        "text",
        ""
    )
    temp = (
        now.get("temp", "")
        + u"\N{DEGREE SIGN}"
        + "C"
    )
    wind_dir = now.get(
        "windDir",
        ""
    )
    rain = now.get(
        "precip",
        "0"
    )
    wet = now.get(
        "humidity",
        ""
    )
    # ========================================================
    # 3. 三天天气
    # ========================================================
    response = qweather_get(
        "/v7/weather/3d",
        config,
        {
            "location": location_id
        }
    )
    if response.get("code") != "200":
        print(
            "❌ 三天天气获取失败：",
            response
        )
        sys.exit(1)
    daily = response["daily"][0]
    max_temp = (
        daily.get(
            "tempMax",
            ""
        )
        + u"\N{DEGREE SIGN}"
        + "C"
    )
    min_temp = (
        daily.get(
            "tempMin",
            ""
        )
        + u"\N{DEGREE SIGN}"
        + "C"
    )
    sunrise = daily.get(
        "sunrise",
        ""
    )
    sunset = daily.get(
        "sunset",
        ""
    )
    # ========================================================
    # 4. 紫外线
    # ========================================================
    uv = "无"
    try:
        response = qweather_get(
            "/v7/indices/1d",
            config,
            {
                "location": location_id,
                "type": "5"
            }
        )
        if response.get("code") == "200":
            if response.get("daily"):
                uv = response["daily"][0].get(
                    "level",
                    "无"
                )
    except Exception as e:
        print(
            "紫外线获取失败：",
            e
        )
    # ========================================================
    # 5. 24小时降雨概率
    # ========================================================
    rain_prob = ""
    try:
        response = qweather_get(
            "/v7/weather/24h",
            config,
            {
                "location": location_id
            }
        )
        if response.get("code") == "200":
            if response.get("hourly"):
                rain_prob = response["hourly"][0].get(
                    "pop",
                    ""
                )
    except Exception as e:
        print(
            "降雨概率获取失败：",
            e
        )
    # ========================================================
    # 6. 空气质量
    # ========================================================
    pm2p5 = ""
    try:
        response = qweather_get(
            "/v7/air/now",
            config,
            {
                "location": location_id
            }
        )
        if response.get("code") == "200":
            pm2p5 = response["now"].get(
                "pm2p5",
                ""
            )
    except Exception as e:
        print(
            "空气质量获取失败：",
            e
        )
    # ========================================================
    # 7. 生活建议
    # ========================================================
    proposal = ""
    try:
        index_type = random.randint(
            1,
            16
        )
        response = qweather_get(
            "/v7/indices/1d",
            config,
            {
                "location": location_id,
                "type": str(index_type)
            }
        )
        if response.get("code") == "200":
            if response.get("daily"):
                proposal = response["daily"][0].get(
                    "text",
                    ""
                )
    except Exception as e:
        print(
            "生活建议获取失败：",
            e
        )
    # ========================================================
    # 完成
    # ========================================================
    print("====================================")
    print("✅ 天气数据获取成功")
    print("天气：", weather)
    print("温度：", temp)
    print("最高温：", max_temp)
    print("最低温：", min_temp)
    print("风向：", wind_dir)
    print("降雨：", rain)
    print("降雨概率：", rain_prob)
    print("湿度：", wet)
    print("紫外线：", uv)
    print("日出：", sunrise)
    print("日落：", sunset)
    print("PM2.5：", pm2p5)
    print("生活建议：", proposal)
    print("====================================")
    return (
        weather,
        temp,
        max_temp,
        min_temp,
        wind_dir,
        rain,
        rain_prob,
        wet,
        uv,
        sunrise,
        sunset,
        pm2p5,
        proposal
    )
# ============================================================
# 彩虹屁
# ============================================================
def get_tianhang(config):
    try:
        key = config["tian_api"]
        url = (
            "https://apis.tianapi.com/caihongpi/index"
            "?key={}"
        ).format(
            key
        )
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/150.0.0.0 Safari/537.36"
            )
        }
        r = get(
            url,
            headers=headers,
            timeout=15
        )
        print(
            "天行彩虹屁 HTTP 状态码：",
            r.status_code
        )
        print(
            "天行彩虹屁原始返回：",
            repr(r.text[:1500])
        )
        response = r.json()
        if (
            response.get("code") == 200
            and response.get("result")
            and response["result"].get("list")
        ):
            chp = response["result"]["list"][0].get(
                "content",
                ""
            )
        else:
            chp = ""
    except Exception as e:
        print(
            "彩虹屁获取失败：",
            e
        )
        chp = ""
    return chp
# ============================================================
# 生日
# ============================================================
def get_birthday(
    birthday,
    year,
    today
):
    birthday_year = birthday.split("-")[0]
    if birthday_year[0] == "r":
        r_mouth = int(
            birthday.split("-")[1]
        )
        r_day = int(
            birthday.split("-")[2]
        )
        try:
            year_date = ZhDate(
                year,
                r_mouth,
                r_day
            ).to_datetime().date()
        except TypeError:
            print(
                "请检查生日的日子是否在今年存在"
            )
            sys.exit(1)
    else:
        birthday_month = int(
            birthday.split("-")[1]
        )
        birthday_day = int(
            birthday.split("-")[2]
        )
        year_date = date(
            year,
            birthday_month,
            birthday_day
        )
    if today > year_date:
        if birthday_year[0] == "r":
            r_last_birthday = ZhDate(
                year + 1,
                r_mouth,
                r_day
            ).to_datetime().date()
            birth_date = date(
                year + 1,
                r_last_birthday.month,
                r_last_birthday.day
            )
        else:
            birth_date = date(
                year + 1,
                birthday_month,
                birthday_day
            )
        birth_day = str(
            birth_date.__sub__(
                today
            )
        ).split(" ")[0]
    elif today == year_date:
        birth_day = 0
    else:
        birth_date = year_date
        birth_day = str(
            birth_date.__sub__(
                today
            )
        ).split(" ")[0]
    return birth_day
# ============================================================
# 金山词霸
# ============================================================
def get_ciba():
    note_ch = ""
    note_en = ""
    try:
        url = "http://open.iciba.com/dsapi/"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/150.0.0.0 Safari/537.36"
            )
        }
        r = get(
            url,
            headers=headers,
            timeout=15
        )
        res = r.json()
        note_en = res["content"]
        note_ch = res["note"]
    except Exception as e:
        print(
            "词霸获取失败：",
            e
        )
    return note_ch, note_en
# ============================================================
# 天行每日一句
# ============================================================
def get_tian_note(config):
    note_ch = ""
    note_en = ""
    try:
        key = config.get(
            "tian_api",
            ""
        )
        url = (
            "https://apis.tianapi.com/everyday/index"
            "?key={}"
        ).format(
            key
        )
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/150.0.0.0 Safari/537.36"
            )
        }
        response = get(
            url,
            headers=headers,
            timeout=15
        )
        print(
            "天行金句 HTTP 状态码：",
            response.status_code
        )
        print(
            "天行金句接口原始返回：",
            response.text
        )
        result = response.json()
        if (
            result.get("code") == 200
            and result.get("result")
        ):
            item = result["result"]
            note_en = item.get(
                "content",
                ""
            )
            note_ch = item.get(
                "note",
                ""
            )
    except Exception as e:
        print(
            "❌ 天行金句获取异常：",
            e
        )
    if not note_ch:
        note_ch = "保持热爱，奔赴山海"
    if not note_en:
        note_en = "Keep loving, keep going."
    return note_ch, note_en
# ============================================================
# 微信模板消息
# ============================================================
def send_message(
    to_user,
    accessToken,
    region_name,
    weather,
    temp,
    wind_dir,
    rain,
    rain_prob,
    wet,
    uv,
    note_ch,
    note_en,
    max_temp,
    min_temp,
    sunrise,
    sunset,
    pm2p5,
    proposal,
    chp,
    config,
    yq,
    horoscope_data
):
    url = (
        "https://api.weixin.qq.com/cgi-bin/message/template/send"
        "?access_token={}"
    ).format(
        accessToken
    )
    week_list = [
        "星期日",
        "星期一",
        "星期二",
        "星期三",
        "星期四",
        "星期五",
        "星期六"
    ]
    os.environ["TZ"] = "Asia/Shanghai"
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = date(
        year,
        month,
        day
    )
    week = week_list[
        today.isoweekday() % 7
    ]
    # ========================================================
    # 纪念日
    # ========================================================
    commemoration_data = get_commemoration_data(
        today,
        config
    )
    # ========================================================
    # 倒计时
    # ========================================================
    countdown_data = get_countdown_data(
        today,
        config
    )
    # ========================================================
    # 生日
    # ========================================================
    birthdays = {}
    for k, v in config.items():
        if k.startswith("birth"):
            birthdays[k] = v
    # ========================================================
    # 模板数据
    # ========================================================
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {
                "value": "{} {}".format(
                    today,
                    week
                ),
                "color": color(
                    "color_date",
                    config
                )
            },
            "region": {
                "value": region_name,
                "color": color(
                    "color_region",
                    config
                )
            },
            "weather": {
                "value": weather,
                "color": color(
                    "color_weather",
                    config
                )
            },
            "temp": {
                "value": temp,
                "color": color(
                    "color_temp",
                    config
                )
            },
            "wind": {
                "value": wind_dir,
                "color": color(
                    "color_wind",
                    config
                )
            },
            "rain": {
                "value": rain,
                "color": color(
                    "color_weather",
                    config
                )
            },
            "rain_prob": {
                "value": rain_prob,
                "color": color(
                    "color_weather",
                    config
                )
            },
            "wet": {
                "value": wet,
                "color": color(
                    "color_weather",
                    config
                )
            },
            "uv": {
                "value": uv,
                "color": color(
                    "color_weather",
                    config
                )
            },
            "note_en": {
                "value": note_en,
                "color": color(
                    "color_note_en",
                    config
                )
            },
            "note_ch": {
                "value": note_ch,
                "color": color(
                    "color_note_ch",
                    config
                )
            },
            "max_temp": {
                "value": max_temp,
                "color": color(
                    "color_max_temp",
                    config
                )
            },
            "min_temp": {
                "value": min_temp,
                "color": color(
                    "color_min_temp",
                    config
                )
            },
            "sunrise": {
                "value": sunrise,
                "color": color(
                    "color_sunrise",
                    config
                )
            },
            "sunset": {
                "value": sunset,
                "color": color(
                    "color_sunset",
                    config
                )
            },
            "pm2p5": {
                "value": pm2p5,
                "color": color(
                    "color_pm2p5",
                    config
                )
            },
            "proposal": {
                "value": proposal,
                "color": color(
                    "color_proposal",
                    config
                )
            },
            "chp": {
                "value": chp,
                "color": color(
                    "color_chp",
                    config
                )
            },
            "yq": {
                "value": yq,
                "color": color(
                    "color_yq",
                    config
                )
            }
        }
    }
    # ========================================================
    # 星座
    # ========================================================
    for key, value in horoscope_data.items():
        data["data"][key] = {
            "value": value,
            "color": color(
                "color_{}".format(key),
                config
            )
        }
    # ========================================================
    # 纪念日
    # ========================================================
    for key, value in commemoration_data.items():
        data["data"][key] = {
            "value": value,
            "color": color(
                "color_{}".format(key),
                config
            )
        }
    # ========================================================
    # 倒计时
    # ========================================================
    for key, value in countdown_data.items():
        data["data"][key] = {
            "value": value,
            "color": color(
                "color_{}".format(key),
                config
            )
        }
    # ========================================================
    # 生日
    # ========================================================
    for key, value in birthdays.items():
        birth_day = get_birthday(
            value["birthday"],
            year,
            today
        )
        if birth_day == 0:
            birthday_data = (
                "今天{}生日哦，祝{}生日快乐！"
            ).format(
                value["name"],
                value["name"]
            )
        else:
            birthday_data = (
                "距离{}的生日还有{}天"
            ).format(
                value["name"],
                birth_day
            )
        data["data"][key] = {
            "value": birthday_data,
            "color": color(
                "color_{}".format(key),
                config
            )
        }
    # ========================================================
    # 发送微信
    # ========================================================
    headers = {
        "Content-Type": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        )
    }
    print("====================================")
    print("正在发送微信模板消息……")
    print("发送用户：", to_user)
    print("模板 ID：", config.get("template_id"))
    print("====================================")
    try:
        r = post(
            url,
            headers=headers,
            json=data,
            timeout=15
        )
        print(
            "微信模板消息 HTTP 状态码：",
            r.status_code
        )
        print(
            "微信模板消息原始返回：",
            r.text
        )
        response = r.json()
    except Exception as e:
        print(
            "❌ 微信模板消息请求失败：",
            e
        )
        sys.exit(1)
    print(
        "微信模板消息完整返回：",
        response
    )
    errcode = response.get(
        "errcode"
    )
    errmsg = response.get(
        "errmsg",
        ""
    )
    if errcode == 0:
        print("====================================")
        print("✅ 微信模板消息推送成功！")
        print("====================================")
    else:
        print("====================================")
        print("❌ 微信模板消息推送失败")
        print("errcode：", errcode)
        print("errmsg：", errmsg)
        print("====================================")
        sys.exit(1)
# ============================================================
# 主处理
# ============================================================
def handler(
    event,
    context
):
    # ========================================================
    # 读取配置
    # ========================================================
    try:
        with open(
            "config.txt",
            encoding="utf-8"
        ) as f:
            config = eval(
                f.read()
            )
    except FileNotFoundError:
        print(
            "❌ 找不到 config.txt"
        )
        sys.exit(1)
    except SyntaxError:
        print(
            "❌ config.txt 格式错误"
        )
        sys.exit(1)
    except Exception as e:
        print(
            "❌ 读取 config.txt 失败：",
            e
        )
        sys.exit(1)
    print("====================================")
    print("开始执行每日推送")
    print("====================================")
    # ========================================================
    # 检查 API Host
    # ========================================================
    qweather_api_host = config.get(
        "qweather_api_host",
        ""
    ).strip()
    if not qweather_api_host:
        print("❌ 缺少 qweather_api_host")
        print("")
        print("请在 config.txt 中加入：")
        print(
            '"qweather_api_host": "你的专属API Host",'
        )
        print("")
        print(
            "例如："
        )
        print(
            '"qweather_api_host": "abc123.xx.qweatherapi.com",'
        )
        sys.exit(1)
    print(
        "和风天气 API Host：",
        qweather_api_host
    )
    # ========================================================
    # 微信 Access Token
    # ========================================================
    accessToken = get_access_token(
        config
    )
    # ========================================================
    # 用户
    # ========================================================
    users = config["user"]
    # ========================================================
    # 地区
    # ========================================================
    region = config["region"]
    # ========================================================
    # 天气
    # ========================================================
    (
        weather,
        temp,
        max_temp,
        min_temp,
        wind_dir,
        rain,
        rain_prob,
        wet,
        uv,
        sunrise,
        sunset,
        pm2p5,
        proposal
    ) = get_weather(
        region,
        config
    )
    # ========================================================
    # 每日一句
    # ========================================================
    note_ch, note_en = get_tian_note(
        config
    )
    if not note_ch or not note_en:
        note_ch, note_en = get_ciba()
    if not note_ch:
        note_ch = "保持热爱，奔赴山海"
    if not note_en:
        note_en = "Keep loving, keep going."
    # ========================================================
    # 彩虹屁
    # ========================================================
    chp = get_tianhang(
        config
    )
    # ========================================================
    # 疫情
    # ========================================================
    yq_data = yq(
        region,
        config
    )
    # ========================================================
    # 星座
    # ========================================================
    horoscope_data = get_horoscope(
        config
    )
    # ========================================================
    # 微信推送
    # ========================================================
    for user in users:
        send_message(
            user,
            accessToken,
            region,
            weather,
            temp,
            wind_dir,
            rain,
            rain_prob,
            wet,
            uv,
            note_ch,
            note_en,
            max_temp,
            min_temp,
            sunrise,
            sunset,
            pm2p5,
            proposal,
            chp,
            config,
            yq_data,
            horoscope_data
        )
    time.sleep(5)
    print("====================================")
    print("程序执行结束")
    print("====================================")
# ============================================================
# 程序入口
# ============================================================
if __name__ == "__main__":
    handler(
        event="",
        context=""
    )
