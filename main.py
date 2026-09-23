import requests
import json
from datetime import datetime, date

# 读取配置文件
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


def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    res = requests.get(url, timeout=10)
    data = res.json()
    if "access_token" in data:
        print(f"微信 Access Token: {data}")
        return data["access_token"]
    else:
        print("获取access_token失败", data)
        return None


def get_city_id(city):
    url = f"https://api.qweather.com/v2/city/lookup?location={city}&key={weather_key}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        print("和风城市查询失败")
        return None
    res = resp.json()
    if res["code"] == "200":
        return res["location"][0]["id"]
    else:
        print("获取城市ID失败", res)
        return None


def get_weather_info(city_id):
    now_api = f"https://api.qweather.com/v7/weather/now?location={city_id}&key={weather_key}"
    now_res = requests.get(now_api, timeout=10).json()

    day3_api = f"https://api.qweather.com/v7/weather/3d?location={city_id}&key={weather_key}"
    day3_res = requests.get(day3_api, timeout=10).json()

    sun_api = f"https://api.qweather.com/v7/astronomy/sun?location={city_id}&key={weather_key}"
    sun_res = requests.get(sun_api, timeout=10).json()

    air_api = f"https://api.qweather.com/v7/air/now?location={city_id}&key={weather_key}"
    air_res = requests.get(air_api, timeout=10).json()

    index_api = f"https://api.qweather.com/v7/indices/1d?location={city_id}&key={weather_key}&type=5"
    index_res = requests.get(index_api, timeout=10).json()

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


def calc_countdown():
    today = date.today()
    birth = datetime.strptime(b_date, "%Y-%m-%d").date()
    next_birth = birth.replace(year=today.year)
    if next_birth < today:
        next_birth = next_birth.replace(year=today.year + 1)
    birth_left = (next_birth - today).days

    new_year = date(today.year + 1, 1, 1)
    new_year_left = (new_year - today).days
    return birth_left, new_year_left


def get_ciba_sentence():
    try:
        r = requests.get("http://open.iciba.com/dsapi/", timeout=10)
        j = r.json()
        en = j["content"]
        zh = j["note"]
        return zh, en
    except Exception:
        return ("保持热爱，奔赴山海", "Keep loving, keep going.")


def get_tianxing():
    horo_text = "暂无星座运势"
    zh_sentence = ""
    en_sentence = ""

    # 星座
    try:
        url_horo = f"https://apis.tianapi.com/star/index?key={tx_key}&astro={astro_code}"
        horo_resp = requests.get(url_horo, timeout=10).json()
        if horo_resp["code"] == 200:
            horo_text = horo_resp["result"]["list"][0]["content"]
    except Exception as e:
        print("星座接口异常：", e)

    # 每日中英金句
    try:
        url_sentence = f"https://apis.tianapi.com/everyday/index?key={tx_key}"
        sen_resp = requests.get(url_sentence, timeout=10).json()
        print("天行金句返回：", sen_resp)
        if sen_resp["code"] == 200:
            result = sen_resp["result"]
            en_sentence = result["content"]
            zh_sentence = result["note"]
    except Exception as e:
        print("金句接口异常：", e)

    if not zh_sentence or not en_sentence:
        print("天行金句为空，启用词霸兜底")
        zh_sentence, en_sentence = get_ciba_sentence()

    return horo_text, zh_sentence, en_sentence


def send_msg(token, openid, weather, birth_left, new_year_left, horoscope, zh_sentence, en_sentence):
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
            "sentence_zh": {"value": zh_sentence, "color": cfg["color_note_ch"]},
            "sentence_en": {"value": en_sentence, "color": "#000000"}
        }
    }
    res = requests.post(url, json=post_data, timeout=10)
    print("推送返回：", res.json())


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
    horoscope_text, zh_text, en_text = get_tianxing()
    for user in user_list:
        send_msg(access_token, user, weather_data, birth_left_days, new_year_left_days, horoscope_text, zh_text, en_text)
    print("✅推送完成")
