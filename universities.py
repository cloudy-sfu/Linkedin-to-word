import json
import logging
import os
from datetime import datetime
import Levenshtein
import requests
import numpy as np


def download(file_path, url):
    response = requests.get(url, timeout=3)
    with open(file_path, 'r') as f:
        json.dump(response.json(), f)


def get_universities_list(
        file_path="world_universities_and_domains.json",
        url="https://raw.githubusercontent.com/Hipo/university-domains-list/master/"
            "world_universities_and_domains.json"
):
    if not os.path.exists(file_path):
        download(file_path, url)
    modified_time = os.path.getmtime(file_path)
    modified_days_ago = (datetime.now() - datetime.fromtimestamp(modified_time)).days
    if modified_days_ago > 30:  # file downloaded >30 days ago
        download(file_path, url)
    try:
        with open(file_path, 'r') as g:
            universities_list = json.load(g)
    except json.JSONDecodeError:
        download(file_path, url)
        try:
            with open(file_path, 'r') as g:
                universities_list = json.load(g)
        except json.JSONDecodeError:
            logging.warning("Cannot recognize the format of universities list from "
                            f"{url} so cannot generate the country where universities "
                            f"locate.")
            return {"web_pages": [], "name": "", "alpha_two_code": "",
                    "state-province": "", "domains": [], "country": ""}
    return universities_list


def search_university(search_string, universities_list):
    """
    Searches for the most likely university based on the provided name.
    """
    distances = [
        Levenshtein.distance(search_string, university.get("name", ""))
        for university in universities_list
    ]
    search_result = universities_list[np.argmin(distances)]
    return search_result
