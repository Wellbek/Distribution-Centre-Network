"""Korean geography for the fictional Dasol world: cities, DC sites, land mask, map distance."""
import json
from pathlib import Path

import numpy as np


DATA = Path(__file__).resolve().parents[1] / "data"

# name, province (geoBoundaries ADM1 name), lat, lon, population in thousands (approx. 2024)
CITIES = [
    ("Seoul", "Seoul", 37.5665, 126.9780, 9400), ("Incheon", "Incheon", 37.4563, 126.7052, 3000),
    ("Suwon", "Gyeonggi", 37.2636, 127.0286, 1200), ("Yongin", "Gyeonggi", 37.2411, 127.1776, 1080),
    ("Goyang", "Gyeonggi", 37.6584, 126.8320, 1070), ("Seongnam", "Gyeonggi", 37.4200, 127.1265, 920),
    ("Hwaseong", "Gyeonggi", 37.1995, 126.8312, 950), ("Bucheon", "Gyeonggi", 37.5034, 126.7660, 780),
    ("Namyangju", "Gyeonggi", 37.6360, 127.2165, 730), ("Ansan", "Gyeonggi", 37.3219, 126.8309, 650),
    ("Pyeongtaek", "Gyeonggi", 36.9921, 127.1129, 590), ("Anyang", "Gyeonggi", 37.3943, 126.9568, 550),
    ("Siheung", "Gyeonggi", 37.3800, 126.8029, 520), ("Paju", "Gyeonggi", 37.7600, 126.7800, 500),
    ("Gimpo", "Gyeonggi", 37.6153, 126.7156, 490), ("Uijeongbu", "Gyeonggi", 37.7381, 127.0337, 460),
    ("Gwangju-si", "Gyeonggi", 37.4294, 127.2551, 390), ("Hanam", "Gyeonggi", 37.5393, 127.2149, 330),
    ("Gwangmyeong", "Gyeonggi", 37.4786, 126.8646, 280), ("Gunpo", "Gyeonggi", 37.3616, 126.9352, 260),
    ("Osan", "Gyeonggi", 37.1499, 127.0773, 230), ("Icheon", "Gyeonggi", 37.2720, 127.4350, 220),
    ("Yangju", "Gyeonggi", 37.7853, 127.0458, 250), ("Anseong", "Gyeonggi", 37.0080, 127.2797, 190),
    ("Guri", "Gyeonggi", 37.5943, 127.1296, 190), ("Pocheon", "Gyeonggi", 37.8949, 127.2003, 145),
    ("Yeoju", "Gyeonggi", 37.2983, 127.6370, 115),
    ("Chuncheon", "Gangwon", 37.8813, 127.7298, 285), ("Wonju", "Gangwon", 37.3422, 127.9202, 360),
    ("Gangneung", "Gangwon", 37.7519, 128.8761, 210), ("Donghae", "Gangwon", 37.5247, 129.1143, 89),
    ("Sokcho", "Gangwon", 38.2070, 128.5918, 82), ("Samcheok", "Gangwon", 37.4499, 129.1652, 63),
    ("Taebaek", "Gangwon", 37.1641, 128.9856, 39), ("Hongcheon", "Gangwon", 37.6970, 127.8886, 67),
    ("Cheorwon", "Gangwon", 38.1467, 127.3133, 42), ("Yeongwol", "Gangwon", 37.1836, 128.4617, 37),
    ("Cheongju", "North Chungcheong", 36.6424, 127.4890, 850), ("Chungju", "North Chungcheong", 36.9910, 127.9259, 208),
    ("Jecheon", "North Chungcheong", 37.1326, 128.1910, 130), ("Eumseong", "North Chungcheong", 36.9400, 127.6900, 92),
    ("Jincheon", "North Chungcheong", 36.8550, 127.4350, 85), ("Okcheon", "North Chungcheong", 36.3060, 127.5710, 50),
    ("Daejeon", "Daejeon", 36.3504, 127.3845, 1440), ("Sejong", "Sejong", 36.4800, 127.2890, 390),
    ("Cheonan", "South Chungcheong", 36.8151, 127.1139, 660), ("Asan", "South Chungcheong", 36.7898, 127.0018, 340),
    ("Seosan", "South Chungcheong", 36.7848, 126.4503, 175), ("Dangjin", "South Chungcheong", 36.8898, 126.6459, 170),
    ("Gongju", "South Chungcheong", 36.4465, 127.1190, 100), ("Nonsan", "South Chungcheong", 36.1872, 127.0987, 112),
    ("Boryeong", "South Chungcheong", 36.3334, 126.6127, 97), ("Hongseong", "South Chungcheong", 36.6012, 126.6608, 100),
    ("Taean", "South Chungcheong", 36.7456, 126.2979, 61),
    ("Jeonju", "North Jeolla", 35.8242, 127.1480, 640), ("Iksan", "North Jeolla", 35.9483, 126.9577, 270),
    ("Gunsan", "North Jeolla", 35.9676, 126.7366, 260), ("Jeongeup", "North Jeolla", 35.5699, 126.8559, 105),
    ("Namwon", "North Jeolla", 35.4164, 127.3904, 78), ("Gimje", "North Jeolla", 35.8036, 126.8809, 82),
    ("Gwangju", "Gwangju", 35.1595, 126.8526, 1420), ("Suncheon", "South Jeolla", 34.9506, 127.4872, 275),
    ("Yeosu", "South Jeolla", 34.7604, 127.6622, 272), ("Mokpo", "South Jeolla", 34.8118, 126.3922, 215),
    ("Gwangyang", "South Jeolla", 34.9407, 127.6959, 152), ("Naju", "South Jeolla", 35.0160, 126.7108, 117),
    ("Haenam", "South Jeolla", 34.5733, 126.5990, 65), ("Muan", "South Jeolla", 34.9904, 126.4817, 90),
    ("Goheung", "South Jeolla", 34.6112, 127.2849, 62),
    ("Daegu", "Daegu", 35.8714, 128.6014, 2380), ("Pohang", "North Gyeongsang", 36.0190, 129.3435, 495),
    ("Gumi", "North Gyeongsang", 36.1195, 128.3446, 410), ("Gyeongsan", "North Gyeongsang", 35.8251, 128.7414, 270),
    ("Gyeongju", "North Gyeongsang", 35.8562, 129.2247, 250), ("Andong", "North Gyeongsang", 36.5684, 128.7294, 155),
    ("Gimcheon", "North Gyeongsang", 36.1398, 128.1136, 140), ("Yeongju", "North Gyeongsang", 36.8057, 128.6240, 100),
    ("Sangju", "North Gyeongsang", 36.4109, 128.1590, 94), ("Yeongcheon", "North Gyeongsang", 35.9733, 128.9386, 100),
    ("Mungyeong", "North Gyeongsang", 36.5865, 128.1867, 70), ("Uljin", "North Gyeongsang", 36.9930, 129.4004, 48),
    ("Yeongdeok", "North Gyeongsang", 36.4153, 129.3653, 35), ("Chilgok", "North Gyeongsang", 35.9956, 128.4017, 110),
    ("Busan", "Busan", 35.1796, 129.0756, 3300), ("Ulsan", "Ulsan", 35.5384, 129.3114, 1100),
    ("Changwon", "South Gyeongsang", 35.2280, 128.6811, 1010), ("Gimhae", "South Gyeongsang", 35.2285, 128.8894, 530),
    ("Yangsan", "South Gyeongsang", 35.3350, 129.0372, 355), ("Jinju", "South Gyeongsang", 35.1800, 128.1076, 340),
    ("Geoje", "South Gyeongsang", 34.8806, 128.6211, 240), ("Tongyeong", "South Gyeongsang", 34.8544, 128.4331, 123),
    ("Sacheon", "South Gyeongsang", 35.0037, 128.0642, 110), ("Miryang", "South Gyeongsang", 35.5038, 128.7467, 103),
    ("Haman", "South Gyeongsang", 35.2724, 128.4065, 60), ("Geochang", "South Gyeongsang", 35.6866, 127.9095, 60),
    ("Hadong", "South Gyeongsang", 35.0674, 127.7513, 43), ("Namhae", "South Gyeongsang", 34.8377, 127.8924, 41),
]

# The 60 leasable sites near motorway interchanges and logistics zones (id, name, province, lat, lon); ids match data/road_cache.npz
SITES = [
    ("S01", "Yongin Giheung", "Gyeonggi", 37.245, 127.13), ("S02", "Gimpo Gochon", "Gyeonggi", 37.6, 126.7),
    ("S03", "Yangju Gwangjeok", "Gyeonggi", 37.79, 127.01), ("S04", "Hanam Gamil", "Gyeonggi", 37.555, 127.2),
    ("S05", "Cheonan Seobuk", "South Chungcheong", 36.86, 127.15), ("S06", "Daejeon Daedeok", "Daejeon", 36.42, 127.42),
    ("S07", "Wonju Munmak", "Gangwon", 37.32, 127.82), ("S08", "Iksan Wanggung", "North Jeolla", 35.96, 127.0),
    ("S09", "Gwangju Pyeongdong", "Gwangju", 35.14, 126.76), ("S10", "Gyeongsan Jillyang", "North Gyeongsang", 35.86, 128.79),
    ("S11", "Busan Gangseo", "Busan", 35.11, 128.9), ("S12", "Incheon Namdong", "Incheon", 37.4, 126.7),
    ("S13", "Hwaseong Hyangnam", "Gyeonggi", 37.12, 126.92), ("S14", "Pyeongtaek Poseung", "Gyeonggi", 36.99, 126.86),
    ("S15", "Anseong Wongok", "Gyeonggi", 37.04, 127.18), ("S16", "Namyangju Jingeon", "Gyeonggi", 37.66, 127.18),
    ("S17", "Paju Munsan", "Gyeonggi", 37.85, 126.79), ("S18", "Siheung Banwol", "Gyeonggi", 37.33, 126.74),
    ("S19", "Gwangju-si Opo", "Gyeonggi", 37.36, 127.23), ("S20", "Osan Gajang", "Gyeonggi", 37.17, 127.04),
    ("S21", "Icheon Majang", "Gyeonggi", 37.235, 127.39), ("S22", "Gangneung Gujeong", "Gangwon", 37.72, 128.87),
    ("S23", "Chuncheon Toegye", "Gangwon", 37.85, 127.71), ("S24", "Ulsan Onsan", "Ulsan", 35.44, 129.3),
    ("S25", "Donghae Bukpyeong", "Gangwon", 37.5, 129.08), ("S26", "Chungju Daesowon", "North Chungcheong", 37.01, 127.88),
    ("S27", "Cheongju Osong", "North Chungcheong", 36.63, 127.33), ("S28", "Eumseong Daeso", "North Chungcheong", 36.96, 127.56),
    ("S29", "Jecheon Bongyang", "North Chungcheong", 37.11, 128.13), ("S30", "Okcheon Cheongsan", "North Chungcheong", 36.33, 127.6),
    ("S31", "Sejong Bugang", "Sejong", 36.53, 127.25), ("S32", "Asan Tangjeong", "South Chungcheong", 36.79, 127.05),
    ("S33", "Dangjin Songak", "South Chungcheong", 36.9, 126.72), ("S34", "Seosan Daesan", "South Chungcheong", 36.78, 126.5),
    ("S35", "Nonsan Yeonmu", "South Chungcheong", 36.17, 127.1), ("S36", "Hongseong Galsan", "South Chungcheong", 36.62, 126.61),
    ("S37", "Wanju Bongdong", "North Jeolla", 35.93, 127.17), ("S38", "Gunsan Okseo", "North Jeolla", 35.95, 126.7),
    ("S39", "Jeongeup Buk", "North Jeolla", 35.6, 126.88), ("S40", "Namwon Ijin", "North Jeolla", 35.43, 127.41),
    ("S41", "Naju Bitgaram", "South Jeolla", 35.02, 126.78), ("S42", "Muan Iljo", "South Jeolla", 34.99, 126.47),
    ("S43", "Suncheon Haeryong", "South Jeolla", 34.95, 127.54), ("S44", "Gwangyang Port", "South Jeolla", 34.92, 127.7),
    ("S45", "Jinju Sabong", "South Gyeongsang", 35.17, 128.18), ("S46", "Changwon Jinyeong", "South Gyeongsang", 35.3, 128.72),
    ("S47", "Yangsan Sangbuk", "South Gyeongsang", 35.39, 129.05), ("S48", "Gimhae Hallim", "South Gyeongsang", 35.3, 128.81),
    ("S49", "Miryang Sangnam", "South Gyeongsang", 35.48, 128.76), ("S50", "Geochang Namha", "South Gyeongsang", 35.68, 127.94),
    ("S51", "Gyeongju Oedong", "North Gyeongsang", 35.75, 129.29), ("S52", "Pohang Yeongil", "North Gyeongsang", 36.0, 129.39),
    ("S53", "Gumi Sandong", "North Gyeongsang", 36.15, 128.43), ("S54", "Gimcheon Eomo", "North Gyeongsang", 36.12, 128.15),
    ("S55", "Andong Pungsan", "North Gyeongsang", 36.59, 128.58), ("S56", "Yeongcheon Geumho", "North Gyeongsang", 35.94, 128.88),
    ("S57", "Chilgok Waegwan", "North Gyeongsang", 35.99, 128.4), ("S58", "Daegu Dalseong", "Daegu", 35.77, 128.47),
    ("S59", "Sangju Cheongni", "North Gyeongsang", 36.39, 128.18), ("S60", "Yeongju Munsu", "North Gyeongsang", 36.78, 128.6),
]

# Today's 12 DCs and their lease ends: the sites a planner picks by p-median on road km with every store within one
# driver-day and no DC above the store cap (prep/current_network.py); the baseline is exempt from the store minimum
CURRENT = {
    "S22": "2027-03-31", "S16": "2028-06-30", "S02": "2029-09-30",
    "S19": "2027-12-31", "S13": "2030-03-31", "S60": "2028-12-31",
    "S35": "2031-06-30", "S58": "2029-03-31", "S51": "2030-09-30",
    "S11": "2027-09-30", "S41": "2031-03-31", "S44": "2028-09-30",
}

CAPITAL = {"Seoul", "Gyeonggi", "Incheon"}
METRO = {"Busan", "Daegu", "Daejeon", "Gwangju", "Ulsan", "Sejong"}
MOUNTAIN = {"Gangwon", "North Gyeongsang"}


def site_cost_factor(province):
    # Capital-region premium, metro neutral-ish, regional discount around the 150 M mean
    if province in CAPITAL:
        return 1.20
    if province in METRO:
        return 1.05
    return 0.88


def load_land():
    # Mainland and nearby islands without Jeju; rings as lon/lat arrays per province
    g = json.loads((DATA / "korea_adm1.geojson").read_text())
    provinces = []
    for f in g["features"]:
        name = f["properties"]["shapeName"]
        if name == "Jeju":
            continue
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        provinces.append((name, [np.asarray(p[0]) for p in polys]))
    return provinces


def in_ring(lon, lat, ring):
    # Even-odd ray casting, vectorised over points
    x, y = ring[:, 0], ring[:, 1]
    x2, y2 = np.roll(x, -1), np.roll(y, -1)
    inside = np.zeros(lon.shape, bool)
    for xa, ya, xb, yb in zip(x, y, x2, y2):
        cond = (ya > lat) != (yb > lat)
        xint = xa + (lat - ya) * (xb - xa) / np.where(yb - ya == 0, 1e-12, yb - ya)
        inside ^= cond & (lon < xint)
    return inside


def province_of(lon, lat, provinces):
    # Province name per point, "" when at sea
    out = np.full(lon.shape, "", dtype=object)
    # Smallest first: the outer rings of Gyeonggi, North Gyeongsang and South Jeolla also cover Seoul, Daegu and Gwangju
    area = lambda rings: sum(abs(np.dot(r[:, 0], np.roll(r[:, 1], 1)) - np.dot(r[:, 1], np.roll(r[:, 0], 1))) for r in rings)
    for name, rings in sorted(provinces, key=lambda pr: area(pr[1])):
        m = np.zeros(lon.shape, bool)
        for r in rings:
            m |= in_ring(lon, lat, r)
        out[m & (out == "")] = name
    return out


def haversine(lat1, lon1, lat2, lon2):
    # Great-circle km, broadcasting
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.minimum(a, 1.0)))

