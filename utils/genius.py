import datetime
import json
import os
import time
import re
from difflib import SequenceMatcher

import requests
from bs4 import BeautifulSoup, FeatureNotFound

from utils import custom_requests


def generate_bs4_soup(url: str, **kwargs):
    """Returns a `BeautifulSoup` from the given `url`.
    Tries to use `lxml` as the parser if available, otherwise `html.parser`
    """
    r = custom_requests.get(url)
    try:
        soup = BeautifulSoup(r.text, features="lxml", **kwargs)
    except FeatureNotFound:
        soup = BeautifulSoup(r.text, features="html.parser", **kwargs)
    return soup


def compare_strings(string1, string2):
    one_in_two = re.sub(r'\W+', '', string1).lower() in re.sub(r'\W+', '', string2).lower()
    two_in_one = re.sub(r'\W+', '', string2).lower() in re.sub(r'\W+', '', string1).lower()
    return one_in_two or two_in_one


def get_structure_and_image(artist: str, title: str, verbose=False):
    SEARCH_ENDPOINT = f"https://genius.com/api/search/multi?q={artist} {title.split(' (')[0].split(' -')[0]}"
    # params = {"q": f"{artist} {title.split(' (')[0]}"}
    cookies = {
        "obuid": "e3ee67e0-7df9-4181-8324-d977c6dc9250",
    }
    t1 = time.time()
    r = custom_requests.get(SEARCH_ENDPOINT, cookies=cookies)
    if verbose:
        print(f"Made request in {time.time() - t1}s")  # 43.33251452445984s # 0.8624658584594727s
        json.dump(r.json(), open("data.json", "w", encoding="utf-8"), ensure_ascii=False)
    if not r.ok:
        print("Request failed, trying again...")
        return None, None
    request_data = r.json()["response"]["sections"][1]["hits"]
    if not request_data:
        if verbose:
            print("No data given by request, trying again...")
            print('artist - ', artist)
            print('title - ', title.split(' (')[0].split(' -')[0])
        return None, None
    url = None
    for result in request_data :
        if verbose :
            print(result)
        if 'Genius' not in result['result']['artist_names'] and compare_strings(result['result']['artist_names'], artist) :
            url = result["result"]["url"]
            song_art = result["result"]["song_art_image_url"]
            break
    if not url:
        print("No url found, trying again...")
        return None, None
    if verbose:
        print(f"Found url in {time.time() - t1}s")  # 43.33361029624939s
    soup = generate_bs4_soup(url)
    if verbose:
        print(f"Made soup in {time.time() - t1}s")  # 85.57257771492004s
    els = soup.find_all("div", attrs={"data-lyrics-container": True})
    if not els:
        print("No lyrics found, trying again...")
        return None, None
    lrc = ""
    for el in els:
        lrc += el.get_text(separator="\n", strip=True).replace("\n[", "\n\n[")
    print("lrc done")

    return lrc, song_art


def get_first_line_of_chorus_and_image(artist: str, title: str, skips: int):
    identification = {"Chorus": 'en', "Hook": 'en', "Coro": 'es', "Estribillo": 'es', "Refrain": 'fr', "Ritornello": 'it'}
    trials = 0
    lrc, song_art = get_structure_and_image(artist, title)
    while lrc is None and trials < 5:
        lrc, song_art = get_structure_and_image(artist, title)
        trials += 1
    if lrc is None:
        return None, None
    lines = lrc.split("\n")
    start = -1
    for key in identification:
        for i in range(len(lines)):
            if f"[{key.lower()}" in lines[i].lower() and skips == 0:
                start = i
                break
            elif f"[{key.lower()}" in lines[i].lower():
                skips -= 1
    try:
        print(lines[start + 1])
    except Exception:
        print('Print Error')
    return lines[start + 1], song_art


def find_time_for_line(string: str, file: str, duration: int):
    def get_timestamp_from_string(string: str):
        timestamp = string.split("]")[0][1:]
        return datetime.datetime.strptime(timestamp, "%M:%S.%f").time()

    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()

    if string is None :
        return datetime.time(0, 0, 0)

    with open(f"{os.getcwd()}/data/lrc/" + file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if '[length' in lines[-1]: # No lyrics available
            return datetime.time(0, 0, 0)
        ratio = 0.6
        found = False
        while not found :
            for i, line in enumerate(lines):
                if i < 4:
                    continue
                if similar(line, string) >= ratio:
                    t = get_timestamp_from_string(line)
                    found = True
                    break
            else:
                ratio -= 0.1

    if i == 4:  # First line of lrc file
        return datetime.time(0, 0, 0)

    start = (datetime.datetime.combine(datetime.date.today(), t) - datetime.timedelta(seconds=duration)).time()
    print(f"Start: {start}")

    if datetime.time(0, 0, duration) > t:
        print("Need to skip one more time")
        return None

    return start
