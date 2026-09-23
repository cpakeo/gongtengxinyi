import requests
import json
from datetime import datetime, date

# 读取配置
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

app_id = cfg["app_id"]
app_secret = cfg["app_secret"]
template_id = cfg["template_id"]
user_list = cfg["user"]
weather_key = cfg["weather_key"]
tx_key = cfg["tianxing_key"]
city_name = cfg["city"]
b_name = cfg["birthday_name"]
b_date = cfg["birthday"]
astro_code = cfg["astro"]


# 获取微信 access_token
def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    res = requests.get(url)
    data = res.json()
    if "access_token" in data:
        print(f"微信 Access Token 接口返回: {data}")
        return data["access_token"]
    else:
        print("获取token失败", data)
        return None


# 获取和风城市ID
def get_city_id(city):
    url = f"https://api.qweather.com/v2/city/lookup?location={city}&key={weather_key}"
    resp = requests.get(url)
    print(f"和风天气请求，HTTP状态码：{resp.status_code}")
    if resp.status_code != 200:
        print("和风城市查询请求失败")
        return None
    res = resp.json()
    if res["code"] == "200":
        return res["location"][0]["id"]
    else:
        print("获取城市id失败", res)
        return None


# 获取天气全部数据（实况、空气质量、日出日落、生活指数）
def get_weather_info(city_id):
    # 实况天气
    now_api = f"https://api.qweather.com/v7/weather/now?location={city_id}&key={weather_key}"
    now_res = requests.get(now_api).json()
    # 3天预报
    day3_api = f"https://api.qweather.com/v7/weather/3d?location={city_id}&key={weather_key}"
    day3_res = requests.get(day3_api).json()
    # 日出日落
    sun_api = f"https://api.qweather.com/v7/astronomy/sun?location={city_id}&key={weather_key}"
    sun_res = requests.get(sun_api).json()
    # 空气质量（PM2.5）
    air_api = f"https://api.qweather.com/v7/air/now?location={city_id}&key={weather_key}"
    air_res = requests.get(air_api).json()
    # 生活指数提示
    index_api = f"https://api.qweather.com/v7/indices/1d?location={city_id}&key={weather_key}&type=5"
    index_res = requests.get(index_api).json()

    now = now_res["now"]
    today = day3_res["daily"][0]
    sunrise = sun_res["sunrise"].split("T")[1]
    sunset = sun_res["sunset"].split("T")[1]
    pm25 = air_res["now"].get("pm2p5", "--")
    tip_text = index_res["daily"][0]["text"]

    data = {
        "date": datetime.now().strftime("%m-%d"),
        "city": city_name,
        "weather": now["text"],
        "temp": now["temp"],
        "maxTemperature": today["tempMax"],
        "minTemperature": today["tempMin"],
        "windDir": now["windDir"],
        "precip": now["precip"],
        "pop": today["pop"],
        "humidity": now["humidity"],
        "uv": today["uvIndex"],
        "pm25": pm25,
        "sunrise": sunrise,
        "sunset": sunset,
        "tip": tip_text
    }
    return data


# 计算生日倒计时、距离新年倒计时
def calc_countdown():
    today = date.today()
    # 生日倒计时
    birth = datetime.strptime(b_date, "%Y-%m-%d").date()
    next_birth = birth.replace(year=today.year)
    if next_birth < today:
        next_birth = next_birth.replace(year=today.year + 1)
    birth_left = (next_birth - today).days

    # 距离下一年元旦倒计时
    new_year = date(today.year + 1, 1, 1)
    new_year_left = (new_year - today).days
    return birth_left, new_year_left


# 天行API获取巨蟹座星座运势 + 每日金句
def get_tianxing():
    try:
        url_horo = f"https://api.tianapi.com/star/index?key={tx_key}&astro={astro_code}"
        horo_resp = requests.get(url_horo, timeout=10).json()
        horo_text = horo_resp["newslist"][0]["content"]
    except Exception as e:
        print("星座获取失败：", e)
        horo_text = "暂无星座运势"

    try:
        url_sentence = f"https://api.tianapi.com/en/index?key={tx_key}"
        sen_resp = requests.get(url_sentence, timeout=10).json()
        zh = sen_resp["newslist"][0]["zh"]
    except Exception as e:
        print("金句获取失败：", e)
        zh = ""
    return horo_text, zh


# 推送微信模板消息
def send_msg(token, openid, weather, birth_left, new_year_left, horoscope, zh_sentence):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    post_data = {
        "touser": openid,
        "template_id": template_id,
        "data": {
            "first": {"value": "新一，早上好啊🌞", "color": "#000000"},
            "date": {"value": weather["date"], "color": cfg["color_date"]},
            "region": {"value": weather["city"], "color": cfg["color_region"]},
            "weather": {"value": weather["weather"], "color": cfg["color_weather"]},
            "temp_now": {"value": f"{weather['temp']}℃", "color": cfg["color_temp"]},
            "temp_max": {"value": f"{weather['maxTemperature']}℃", "color": cfg["color_max_temp"]},
            "temp_min": {"value": f"{weather['minTemperature']}℃", "color": cfg["color_min_temp"]},
            "wind": {"value": weather["windDir"], "color": cfg["color_wind"]},
            "precip": {"value": f"{weather['precip']}mm", "color": "#000000"},
            "pop": {"value": f"{weather['pop']}%", "color": "#000000"},
            "humidity": {"value": f"{weather['humidity']}%", "color": "#000000"},
            "uv": {"value": f"{weather['uv']}（紫外线指数）", "color": "#000000"},
            "pm25": {"value": weather["pm25"], "color": "#000000"},
            "sunrise": {"value": weather["sunrise"], "color": "#000000"},
            "sunset": {"value": weather["sunset"], "color": "#000000"},
            "horoscope": {"value": horoscope, "color": "#000000"},
            "birth_day": {"value": f"距离{b_name}的生日还有{birth_left}天", "color": "#000000"},
            "new_year": {"value": f"{new_year_left}", "color": "#000000"},
            "tip": {"value": weather["tip"], "color": "#000000"},
            "sentence": {"value": zh_sentence, "color": cfg["color_note_ch"]}
        }
    }
    res = requests.post(url, json=post_data)
    print("推送结果：", res.json())


if __name__ == "__main__":
    print("=====开始执行每日推送=====")
    access_token = get_access_token()
    if not access_token:
        exit(1)
    cityid = get_city_id(city_name)
    if not cityid:
        exit(1)
    weather_data = get_weather_info(cityid)
    birth_left_days, new_year_left_days = calc_countdown()
    horoscope_text, sentence_zh = get_tianxing()
    for user in user_list:
        send_msg(access_token, user, weather_data, birth_left_days, new_year_left_days, horoscope_text, sentence_zh)
    print("✅推送完成")
