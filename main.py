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
love_start = cfg["love_start_date"]
b1_name = cfg["birthday1_name"]
b1_date = cfg["birthday1"]
b2_name = cfg["birthday2_name"]
b2_date = cfg["birthday2"]
astro_name = cfg["astro"]

# 星期映射
week_map = {0:"星期一",1:"星期二",2:"星期三",3:"星期四",4:"星期五",5:"星期六",6:"星期日"}

# 获取微信access_token
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
    print(f"返回内容：{resp.text}")
    if resp.status_code != 200:
        print("和风城市查询请求失败")
        return None
    res = resp.json()
    if res["code"] == "200":
        return res["location"][0]["id"]
    else:
        print("获取城市id失败", res)
        return None

# 获取全部天气数据（实况、3天预报、日出日落、生活指数）
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
    # 生活指数（穿衣提示）
    index_api = f"https://api.qweather.com/v7/indices/1d?location={city_id}&key={weather_key}&type=3"
    index_res = requests.get(index_api).json()

    now = now_res["now"]
    today_day = day3_res["daily"][0]
    sunrise = sun_res["sunrise"].split("T")[1]
    sunset = sun_res["sunset"].split("T")[1]
    dress_tip = index_res["daily"][0]["text"]

    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "week": week_map[datetime.now().weekday()],
        "city": city_name,
        "weather": now["text"],
        "temp": now["temp"],
        "maxTemperature": today_day["tempMax"],
        "minTemperature": today_day["tempMin"],
        "windDir": now["windDir"],
        "windScale": now["windScale"],
        "precip": now["precip"],
        "pop": today_day["pop"],
        "humidity": now["humidity"],
        "uv": today_day["uvIndex"],
        "sunrise": sunrise,
        "sunset": sunset,
        "dress_tip": dress_tip
    }
    return data

# 计算天数：恋爱天数、生日倒计时
def calc_day_count():
    today = date.today()
    # 在一起天数
    love_dt = datetime.strptime(love_start, "%Y-%m-%d").date()
    love_days = (today - love_dt).days
    # 生日1倒计时
    b1 = datetime.strptime(b1_date, "%Y-%m-%d").date()
    next_b1 = b1.replace(year=today.year)
    if next_b1 < today:
        next_b1 = next_b1.replace(year=today.year+1)
    b1_left = (next_b1 - today).days
    # 生日2倒计时
    b2 = datetime.strptime(b2_date, "%Y-%m-%d").date()
    next_b2 = b2.replace(year=today.year)
    if next_b2 < today:
        next_b2 = next_b2.replace(year=today.year+1)
    b2_left = (next_b2 - today).days
    return love_days, b1_left, b2_left

# 天行API：星座运势 + 中英文金句
def get_tianxing_data():
    # 星座运势
    url_horo = f"https://api.tianapi.com/star/index?key={tx_key}&astro={astro_name}"
    horo_resp = requests.get(url_horo).json()
    horoscope = horo_resp["newslist"][0]["content"]
    # 每日一句中英文
    url_sentence = f"https://api.tianapi.com/en/index?key={tx_key}"
    sen_resp = requests.get(url_sentence).json()
    zh_text = sen_resp["newslist"][0]["zh"]
    en_text = sen_resp["newslist"][0]["en"]
    return horoscope, zh_text, en_text

# 发送微信模板消息
def send_wechat_msg(token, openid, weather, love_days, b1_left, b2_left, horoscope, zh_sentence, en_sentence):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    post_data = {
        "touser": openid,
        "template_id": template_id,
        "data": {
            "first": {"value": "xxx早上好呀！", "color": "#000000"},
            "date": {"value": f"{weather['date']} {weather['week']}", "color": cfg["color_date"]},
            "tip": {"value": "今天又是元气满满的一天啦！开心一点！", "color": "#000000"},
            "region": {"value": weather["city"], "color": cfg["color_region"]},
            "weather": {"value": weather["weather"], "color": cfg["color_weather"]},
            "temp_now": {"value": f"{weather['temp']}℃", "color": cfg["color_temp"]},
            "temp_max": {"value": f"{weather['maxTemperature']}℃", "color": cfg["color_max_temp"]},
            "temp_min": {"value": f"{weather['minTemperature']}℃", "color": cfg["color_min_temp"]},
            "wind_info": {"value": f"{weather['windDir']} {weather['windScale']}级", "color": cfg["color_wind"]},
            "precip": {"value": f"{weather['precip']}", "color": "#000000"},
            "pop": {"value": f"{weather['pop']}%", "color": "#000000"},
            "humidity": {"value": f"{weather['humidity']}%", "color": "#000000"},
            "uv": {"value": f"{weather['uv']}", "color": "#000000"},
            "sunrise": {"value": weather["sunrise"], "color": "#000000"},
            "sunset": {"value": weather["sunset"], "color": "#000000"},
            "love_day": {"value": f"{love_days}", "color": "#000000"},
            "birth1": {"value": f"{b1_left}", "color": "#000000"},
            "birth2": {"value": f"{b2_left}", "color": "#000000"},
            "dress_tip": {"value": weather["dress_tip"], "color": "#000000"},
            "horoscope": {"value": horoscope, "color": "#000000"},
            "note_zh": {"value": zh_sentence, "color": cfg["color_note_ch"]},
            "note_en": {"value": en_sentence, "color": cfg["color_note_en"]},
            "footer": {"value": "--来自xxx的问候", "color": "#000000"}
        }
    }
    res = requests.post(url, json=post_data)
    print("推送返回结果：", res.json())

if __name__ == "__main__":
    print("=====开始执行每日推送=====")
    access_token = get_access_token()
    if not access_token:
        exit(1)
    cityid = get_city_id(city_name)
    if not cityid:
        exit(1)
    weather_data = get_weather_info(cityid)
    love_days, b1_left, b2_left = calc_day_count()
    horoscope, zh_note, en_note = get_tianxing_data()
    for wx_user in user_list:
        send_wechat_msg(access_token, wx_user, weather_data, love_days, b1_left, b2_left, horoscope, zh_note, en_note)
    print("✅全部推送任务完成！")
