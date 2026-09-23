import random
import time
from time import localtime
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os


def get_horoscope(astro, tian_key):
    horoscope_data = ""
    try:
        url = "https://apis.tianapi.com/star/index?key={}&astro={}".format(tian_key, astro)
        resp = get(url, timeout=15)
        res_json = resp.json()
        if res_json["code"] == 200:
            horoscope_data = res_json["result"]["content"]
    except Exception as e:
        print("星座接口异常：", e)
    return horoscope_data


def get_tian_note(tian_key):
    note_zh = ""
    note_en = ""
    try:
        url = "https://apis.tianapi.com/everyday/index?key={}".format(tian_key)
        resp = get(url, timeout=15)
        res_json = resp.json()
        if res_json["code"] == 200:
            note_zh = res_json["result"]["content"]
            note_en = res_json["result"]["translation"]
    except Exception as e:
        print("天行金句接口异常：", e)
    return note_zh, note_en


def get_weather(region, config):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config["weather_key"]
    # 城市定位接口
    region_url = "https://api.qweather.com/v2/city/lookup?location={}&key={}".format(region, key)
    response = get(region_url, headers=headers, timeout=15)
    print("【城市查询接口原始返回】", response.text)
    try:
        res_json = response.json()
    except Exception as e:
        print("城市查询接口JSON解析失败！", e)
        sys.exit(1)

    if res_json["code"] == "404":
        print("错误：地区名称无法识别，请修改region！")
        sys.exit(1)
    elif res_json["code"] == "401":
        print("错误：和风天气key无效/过期！")
        sys.exit(1)
    location_id = res_json["location"][0]["id"]

    # 实时天气
    weather_url = "https://api.qweather.com/v7/weather/now?location={}&key={}".format(location_id, key)
    response = get(weather_url, headers=headers, timeout=15)
    print("【实时天气接口原始返回】", response.text)
    res_json = response.json()
    weather = res_json["now"]["text"]
    temp = res_json["now"]["temp"] + "℃"
    wind_dir = res_json["now"]["windDir"]
    wind_scale = res_json["now"]["windScale"]
    humidity = res_json["now"]["humidity"]
    precip = res_json["now"]["precip"]
    uv = res_json["now"]["uvIndex"]

    # 3天预报
    url3d = "https://api.qweather.com/v7/weather/3d?location={}&key={}".format(location_id, key)
    response = get(url3d, headers=headers, timeout=15)
    print("【3天预报接口原始返回】", response.text)
    res3d = response.json()
    max_temp = res3d["daily"][0]["tempMax"] + "℃"
    min_temp = res3d["daily"][0]["tempMin"] + "℃"
    day1_wea = res3d["daily"][0]["textDay"]
    day2_wea = res3d["daily"][1]["textDay"]
    day3_wea = res3d["daily"][2]["textDay"]

    # 空气质量
    air_url = "https://api.qweather.com/v7/air/now?location={}&key={}".format(location_id, key)
    response = get(air_url, headers=headers, timeout=15)
    print("【空气质量接口原始返回】", response.text)
    try:
        res_air = response.json()
        if res_air["code"] == "200":
            pm2p5 = res_air["now"]["pm2p5"]
        else:
            pm2p5 = "无数据"
    except:
        pm2p5 = "无数据"

    return weather, temp, max_temp, min_temp, wind_dir, wind_scale, humidity, precip, uv, pm2p5, day1_wea, day2_wea, day3_wea


def get_birthday_calc(birthday_str, this_year):
    birthday_year, birthday_month, birthday_day = birthday_str.split("-")
    if birthday_year[0] == "r":
        lunar_month = int(birthday_month)
        lunar_day = int(birthday_day)
        target_date = ZhDate(this_year, lunar_month, lunar_day).to_datetime().date()
    else:
        target_date = date(this_year, int(birthday_month), int(birthday_day))
    today = date.today()
    if target_date < today:
        if birthday_year[0] == "r":
            target_date = ZhDate(this_year + 1, lunar_month, lunar_day).to_datetime().date()
        else:
            target_date = date(this_year + 1, int(birthday_month), int(birthday_day))
    diff = (target_date - today).days
    return diff


def send_wechat_msg(access_token, template_id, openid, data):
    send_url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    body = {
        "touser": openid,
        "template_id": template_id,
        "data": data
    }
    res = post(send_url, json=body, timeout=20)
    print("微信推送返回结果：", res.text)
    return res.json()


def get_access_token(appid, appsecret):
    url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}".format(appid, appsecret)
    resp = get(url, timeout=15)
    res = resp.json()
    if "access_token" in res:
        return res["access_token"]
    else:
        print("获取access_token失败", res)
        sys.exit(1)


def handler(event, context):
    # 读取配置
    with open("config.txt", "r", encoding="utf-8") as f:
        config = eval(f.read())

    app_id = config["app_id"]
    app_secret = config["app_secret"]
    template_id = config["template_id"]
    user_list = config["user"]
    weather_key = config["weather_key"]
    tian_key = config["tian_key"]
    region = config["region"]

    # 获取天气
    weather, temp, max_temp, min_temp, wind_dir, wind_scale, humidity, precip, uv, pm2p5, day1_wea, day2_wea, day3_wea = get_weather(region, config)

    # 获取金句
    note_zh, note_en = get_tian_note(tian_key)

    # 获取星座
    horoscope1 = get_horoscope(config["horoscope"], tian_key)

    # 日期
    today = datetime.now()
    date_str = today.strftime("%Y年%m月%d日 %A")

    # 组装模板数据
    msg_data = {
        "first": {"value": "早上好呀！", "color": "#000000"},
        "date": {"value": date_str, "color": config["color_date"]},
        "city": {"value": region, "color": config["color_region"]},
        "weather": {"value": weather, "color": config["color_weather"]},
        "temp": {"value": temp, "color": config["color_temp"]},
        "maxTemperature": {"value": max_temp, "color": config["color_max_temp"]},
        "minTemperature": {"value": min_temp, "color": config["color_min_temp"]},
        "wind": {"value": f"{wind_dir} {wind_scale}级", "color": config["color_wind"]},
        "wet": {"value": f"{humidity}%", "color": "#000000"},
        "pm2p5": {"value": pm2p5, "color": "#000000"},
        "day1_wea": {"value": day1_wea, "color": "#000000"},
        "day2_wea": {"value": day2_wea, "color": "#000000"},
        "day3_wea": {"value": day3_wea, "color": "#000000"},
        "horoscope1": {"value": horoscope1, "color": "#000000"},
        "note_zh": {"value": note_zh, "color": config["color_note_ch"]},
        "note_en": {"value": note_en, "color": config["color_note_en"]},
    }

    # 获取微信token
    access_token = get_access_token(app_id, app_secret)

    # 循环推送多个用户
    for openid in user_list:
        ret = send_wechat_msg(access_token, template_id, openid, msg_data)
        if ret["errcode"] == 0:
            print(f"给 {openid} 推送成功")
        else:
            print(f"给 {openid} 推送失败：{ret}")


if __name__ == "__main__":
    handler("", "")
