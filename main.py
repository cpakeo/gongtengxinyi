import os
import sys
import random
import requests
from datetime import datetime
from zhdate import ZhDate

get = requests.get
post = requests.post

def get_weather(region, config):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config["weather_key"]
    region_url = "https://geoapi.qweather.com/v2/city/lookup?key={}&location={}".format(key, region)
    response = get(region_url, headers=headers, timeout=10)
    print("geoapi原始返回文本：", response.text)
    if response.status_code != 200:
        print("城市查询接口请求失败，http码：", response.status_code)
        sys.exit(1)
    response_json = response.json()
    if response_json["code"] == "404":
        print("推送消息失败，请检查地区名是否有误！")
        sys.exit(1)
    elif response_json["code"] == "401":
        print("推送消息失败，请检查和风天气key是否正确！")
        sys.exit(1)
    else:
        location_id = response_json["location"][0]["id"]
        print("定位城市ID：", location_id)

    weather_url = "https://devapi.qweather.com/v7/weather/now?location={}&key={}".format(location_id, key)
    response = get(weather_url, headers=headers, timeout=10).json()
    print("实时天气返回code：", response["code"])
    weather = response["now"]["text"]
    temp = response["now"]["temp"] + u"\N{DEGREE SIGN}" + "C"
    wind_dir = response["now"]["windDir"]
    rain = response["now"].get("precip", "0") + "mm"
    wet = response["now"].get("humidity", "") + "%"

    url = "https://devapi.qweather.com/v7/weather/3d?location={}&key={}".format(location_id, key)
    response = get(url, headers=headers, timeout=10).json()
    print("3天预报返回code：", response["code"])
    max_temp = response["daily"][0]["tempMax"] + u"\N{DEGREE SIGN}" + "C"
    min_temp = response["daily"][0]["tempMin"] + u"\N{DEGREE SIGN}" + "C"
    sunrise = response["daily"][0]["sunrise"]
    sunset = response["daily"][0]["sunset"]

    uv = "无"
    try:
        uv_url = "https://devapi.qweather.com/v7/indices/1d?location={}&key={}&type=5".format(location_id, key)
        uv_resp = get(uv_url, headers=headers, timeout=10).json()
        if uv_resp["code"] == "200":
            uv = uv_resp["daily"][0].get("level", "无")
    except Exception as e:
        print("紫外线获取失败：", e)
    print("紫外线指数：", uv)

    rain_prob = ""
    try:
        hourly_url = "https://devapi.qweather.com/v7/weather/24h?location={}&key={}".format(location_id, key)
        hourly_resp = get(hourly_url, headers=headers, timeout=10).json()
        if hourly_resp["code"] == "200":
            rain_prob = hourly_resp["hourly"][0].get("pop", "") + "%"
    except Exception as e:
        print("降雨概率获取失败：", e)
    print("降雨概率：", rain_prob)

    url = "https://devapi.qweather.com/v7/air/now?location={}&key={}".format(location_id, key)
    response = get(url, headers=headers, timeout=10).json()
    pm2p5 = ""
    if response["code"] == "200":
        pm2p5 = response["now"].get("pm2p5", "")
    print("PM2.5：", pm2p5)

    id = random.randint(1, 16)
    url = "https://devapi.qweather.com/v7/indices/1d?location={}&key={}&type={}".format(location_id, key, id)
    response = get(url, headers=headers, timeout=10).json()
    proposal = ""
    if response["code"] == "200":
        proposal += response["daily"][0]["text"]

    return weather, temp, max_temp, min_temp, wind_dir, rain, rain_prob, wet, uv, sunrise, sunset, pm2p5, proposal


def get_tianxing_jinju(api_key):
    url = f"https://api.tianapi.com/everyday/index?key={api_key}"
    res = get(url, timeout=10).json()
    note_zh = res["newslist"][0]["content"]
    note_en = res["newslist"][0]["english"]
    return note_zh, note_en

def get_horoscope(api_key, astro):
    url = f"https://api.tianapi.com/star/index?key={api_key}&astro={astro}"
    res = get(url, timeout=10).json()
    return res["newslist"][0]["content"]

def get_access_token(app_id, app_secret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    resp = get(url,timeout=10).json()
    return resp["access_token"]

def send_msg(access_token, template_id, user, data):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    for openid in user:
        body = {
            "touser": openid,
            "template_id": template_id,
            "data": data
        }
        post(url,json=body,timeout=10)

def handler(event, context):
    os.environ['TZ'] = 'Asia/Shanghai'
    with open("config.txt","r",encoding="utf-8") as f:
        config = eval(f.read())

    app_id = config["app_id"]
    app_secret = config["app_secret"]
    template_id = config["template_id"]
    user_list = config["user"]
    weather_key = config["weather_key"]
    tianxing_key = config["tianxing_key"]
    city = config["city"]
    astro = config["astro"]

    # 颜色配置
    color_date = config["color_date"]
    color_region = config["color_region"]
    color_weather = config["color_weather"]
    color_temp = config["color_temp"]
    color_wind = config["color_wind"]
    color_note_en = config["color_note_en"]
    color_note_ch = config["color_note_ch"]
    color_max_temp = config["color_max_temp"]
    color_min_temp = config["color_min_temp"]

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %A")

    weather, temp, max_temp, min_temp, wind_dir, rain, rain_prob, wet, uv, sunrise, sunset, pm2p5, proposal = get_weather(city, config)
    note_zh, note_en = get_tianxing_jinju(tianxing_key)
    horoscope1 = get_horoscope(tianxing_key, astro)

    data = {
        "first": {"value": "早上好呀！"},
        "date": {"value": date_str, "color": color_date},
        "city": {"value": city, "color": color_region},
        "weather": {"value": weather, "color": color_weather},
        "temp": {"value": temp, "color": color_temp},
        "maxTemperature": {"value": max_temp, "color": color_max_temp},
        "minTemperature": {"value": min_temp, "color": color_min_temp},
        "wind": {"value": wind_dir, "color": color_wind},
        "rain": {"value": rain},
        "rain_prob": {"value": rain_prob},
        "wet": {"value": wet},
        "uv": {"value": uv},
        "pm2p5": {"value": pm2p5},
        "horoscope1": {"value": horoscope1},
        "note_zh": {"value": note_zh, "color": color_note_ch},
        "note_en": {"value": note_en, "color": color_note_en},
    }
    access_token = get_access_token(app_id, app_secret)
    send_msg(access_token,template_id,user_list,data)
    print("推送完成！")

if __name__ == "__main__":
    try:
        handler(event="", context="")
    except Exception as err:
        import traceback
        print("====程序崩溃错误详情====")
        print(traceback.format_exc())

