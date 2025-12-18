import asyncio
import io
import json
import os
import re
import time
from urllib.parse import parse_qs, urlparse

import httpx

try:
    import json5
    json_loader = json5.loads
except ImportError:
    json_loader = json.loads

LENS_UPLOAD_ENDPOINT = "https://lens.google.com/v3/upload"
LENS_METADATA_ENDPOINT = "https://lens.google.com/qfmetadata"
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Not-A.Brand";v="8", "Chromium";v="135", "Google Chrome";v="135"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "X-Client-Data": "CIW2yQEIorbJAQipncoBCIH+ygEIkqHLAQiKo8sBCPWYzQEIhaDNAQji0M4BCLPTzgEI19TOAQjy1c4BCJLYzgEIwNjOAQjM2M4BGM7VzgE=",
    "Origin": "https://www.google.com",
    "Referer": "https://www.google.com/",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-User": "?1",
    "Priority": "u=0, i",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}
COOKIE_FILE = "cookies_lens.json"


async def read_image_data(image_path):
    """Reads image data from file."""
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return data
    except:
        return None


def extract_ids_from_url(url_string):
    """Extracts vsrid and lsessionid from URL."""
    try:
        parsed_url = urlparse(url_string)
        query_params = parse_qs(parsed_url.query)
        vsrid = query_params.get("vsrid", [None])[0]
        lsessionid = query_params.get("lsessionid", [None])[0]
        return vsrid, lsessionid
    except:
        return None, None


async def save_cookies(cookies, cookie_file):
    """Saves cookies to JSON file."""
    try:
        cookies_dict = {}
        cookie_jar = getattr(cookies, "jar", cookies)
        if hasattr(cookie_jar, "items"):
            for name, value in cookie_jar.items():
                cookie_obj = cookie_jar.get(name)
                if cookie_obj and hasattr(cookie_obj, "value"):
                    cookies_dict[name] = cookie_obj.value
                elif isinstance(value, str):
                    cookies_dict[name] = value
        elif hasattr(cookie_jar, "__iter__"):
            for cookie in cookie_jar:
                if hasattr(cookie, "name") and hasattr(cookie, "value"):
                    cookies_dict[cookie.name] = cookie.value

        with open(cookie_file, "w") as f:
            json.dump(cookies_dict, f, indent=2)
    except:
        pass


async def load_cookies(cookie_file):
    """Loads cookies from JSON file."""
    try:
        if os.path.exists(cookie_file):
            with open(cookie_file, "r") as f:
                cookies_dict = json.load(f)
                return cookies_dict
        return {}
    except:
        return {}


def parse_text_from_json(metadata_json):
    """Parse text from metadata JSON."""
    try:
        if not isinstance(metadata_json, list) or not metadata_json:
            return ""

        response_container = next(
            (
                item
                for item in metadata_json
                if isinstance(item, list)
                and item
                and item[0] == "fetch_query_formulation_metadata_response"
            ),
            None,
        )
        if response_container is None:
            return ""

        segments_iterable = None
        possible_paths = [
            lambda rc: rc[2][0][0][0],
            lambda rc: rc[1][0][0][0],
            lambda rc: rc[2][0][0],
        ]

        for path_func in possible_paths:
            try:
                candidate_iterable = path_func(response_container)
                if (
                    isinstance(candidate_iterable, list)
                    and candidate_iterable
                    and isinstance(candidate_iterable[0], list)
                ):
                    first_segment = candidate_iterable[0]
                    if len(first_segment) > 1 and isinstance(first_segment[1], list):
                        if (
                            first_segment[1]
                            and isinstance(first_segment[1][0], list)
                            and len(first_segment[1][0]) > 0
                            and isinstance(first_segment[1][0][0], list)
                        ):
                            segments_iterable = candidate_iterable
                            break
            except:
                continue

        if segments_iterable is None:
            return ""

        all_text = []

        for segment_list in segments_iterable:
            if not isinstance(segment_list, list):
                continue

            try:
                if len(segment_list) > 1 and isinstance(segment_list[1], list):
                    word_groups_list = segment_list[1]

                    for word_group in word_groups_list:
                        try:
                            if (
                                isinstance(word_group, list)
                                and len(word_group) > 0
                                and isinstance(word_group[0], list)
                            ):
                                word_list = word_group[0]

                                for word_info in word_list:
                                    try:
                                        if (
                                            isinstance(word_info, list)
                                            and len(word_info) > 3
                                            and isinstance(word_info[1], str)
                                        ):
                                            text = word_info[1]
                                            all_text.append(text)
                                    except:
                                        continue
                        except:
                            continue
            except:
                continue

        return ' '.join(all_text)
    except:
        return ""


async def extract_text_from_image(image_path):
    """Extract text from image using Google Lens."""
    try:
        image_data = await read_image_data(image_path)
        if not image_data:
            return ""

        filename = os.path.basename(image_path)
        _, ext = os.path.splitext(filename.lower())
        content_type = "image/jpeg"
        if ext == ".png":
            content_type = "image/png"
        elif ext == ".webp":
            content_type = "image/webp"
        elif ext == ".gif":
            content_type = "image/gif"

        files = {"encoded_image": (filename, image_data, content_type)}
        params_upload = {
            "hl": "ru",
            "re": "av",
            "vpw": "1903",
            "vph": "953",
            "ep": "gsbubb",
            "st": str(int(time.time() * 1000)),
        }

        loaded_cookies = await load_cookies(COOKIE_FILE)
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        timeout = httpx.Timeout(60.0, connect=15.0)

        async with httpx.AsyncClient(
            cookies=loaded_cookies,
            follow_redirects=True,
            timeout=timeout,
            limits=limits,
            http2=True,
            verify=True,
        ) as client:
            # Upload image
            response_upload = await client.post(
                LENS_UPLOAD_ENDPOINT, headers=HEADERS, files=files, params=params_upload
            )
            await save_cookies(client.cookies, COOKIE_FILE)
            response_upload.raise_for_status()

            final_url = str(response_upload.url)
            vsrid, lsessionid = extract_ids_from_url(final_url)

            if not vsrid or not lsessionid:
                return ""

            await asyncio.sleep(1)

            # Get metadata
            metadata_params = {
                "vsrid": vsrid,
                "lsessionid": lsessionid,
            }
            metadata_headers = HEADERS.copy()
            metadata_headers.update({
                "Accept": "*/*",
                "Referer": final_url,
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Priority": "u=1, i",
            })
            metadata_headers.pop("Upgrade-Insecure-Requests", None)
            metadata_headers.pop("Sec-Fetch-User", None)
            metadata_headers.pop("Cache-Control", None)
            metadata_headers.pop("Origin", None)

            metadata_url_obj = httpx.URL(
                LENS_METADATA_ENDPOINT, params=metadata_params)
            response_metadata = await client.get(metadata_url_obj, headers=metadata_headers)
            await save_cookies(client.cookies, COOKIE_FILE)
            response_metadata.raise_for_status()

            # Parse response
            response_text = response_metadata.text
            if response_text.startswith(")]}'\n"):
                response_text = response_text[5:]
            elif response_text.startswith(")]}'"):
                response_text = response_text[4:]

            metadata_json = json_loader(response_text)
            return parse_text_from_json(metadata_json)

    except:
        return ""


def extract_front_id(text):
    """
    Extract front ID number from text.

    Args:
        text (str): Text from front side of ID

    Returns:
        str: Front ID number or empty string if not found
    """
    if not text:
        return ""

    # Pattern for 12-digit front ID number
    # Patterns to match:
    # - After "Số định danh cá nhân Personal identification number"
    # - After "Số / No . :"
    # - Standalone 12-digit number
    patterns = [
        r'(?:Số định danh cá nhân|Personal identification number)\s*(\d{12})',
        r'(?:Số\s*/\s*No\s*\.?\s*:?)\s*(\d{12})',
        r'\b(\d{12})\b'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    return ""

def extract_back_id(text):
    """
    Extract back ID number from text.

    Args:
        text (str): Text from back side of ID

    Returns:
        str: Back ID number or empty string if not found
    """
    if not text:
        return ""

    # Split by '<<', take the first chunk, get last 12 digits
    parts = text.split("<<")
    if parts:
        candidate = parts[0]
        match = re.search(r'(\d{12})$', candidate)
        if match:
            return match.group(1)

    return ""


def extract_id_number(text):
    """
    Extract ID number (12 digits) from text, regardless of front or back.

    Args:
        text (str): Text from ID card

    Returns:
        str: ID number or empty string if not found
    """
    if not text:
        return ""

    # Normalize: remove spaces around < and << (OCR often adds spaces)
    normalized_text = re.sub(r'\s*<\s*', '<', text)
    
    # Try splitting by '<<' FIRST for back side MRZ (more reliable)
    # MRZ format: IDVNM0990089616089099008961<<9
    # The ID is the last 12 digits before <<
    parts = normalized_text.split("<<")
    if len(parts) > 1:  # Has << separator (back side MRZ)
        candidate = parts[0]
        match = re.search(r'(\d{12})$', candidate)
        if match:
            return match.group(1)
    
    # Also try with < (single) in case OCR misreads <<
    parts_single = normalized_text.split("<")
    if len(parts_single) > 1:
        candidate = parts_single[0]
        match = re.search(r'(\d{12})$', candidate)
        if match:
            return match.group(1)

    # Patterns for front side
    patterns = [
        r'(?:Số định danh cá nhân|Personal identification number)\s*(\d{12})',
        r'(?:Số\s*/\s*No\s*\.?\s*:?)\s*(\d{12})',
        r'\b(\d{12})\b',
    ]

    # Try all patterns
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    return ""


# Synchronous wrapper function
def get_text_from_image(image_path):
    """
    Extract text from image using Google Lens.

    Args:
        image_path (str): Path to the image file

    Returns:
        str: Extracted text from the image
    """
    return asyncio.run(extract_text_from_image(image_path))


# Example usage
if __name__ == "__main__":
    # Test with provided examples
    # text_front = """CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM Độc lập - Tự do - Hạnh phúc SOCIALIST REPUBLIC OF VIET NAM Independence Freedom-Happiness CĂN CƯỚC IDENTITY CARD Số định danh cá nhân Personal identification number 089099008961 Họ , chữ đệm và tên khai sinh / Full name : MAI TUẤN ANH Ngày , tháng , năm sinh/Date of birth : 22/11/1999 Quốc tịch/Nationality : Việt Nam Giới tính / Sex Nam"""

    # text_back = """Nơi cư trú / Place of residence : Ấp Vĩnh Cầu Vĩnh Gia , Trì Tôn , An Giang Nơi đăng ký khai sinh/Place of birth : Vĩnh Gia , Tri Tôn , An Giang Ngày , tháng , năm cấp / Date of issue : 14/04/2025 Ngày , tháng , năm hết hạn / Date of expiry : 22/11/2039 BỘ CÔNG AN/MINISTRY OF PUBLIC SECURITY IDVNM0990089616089099008961<<9 9911226M3911224VNM<<<<<<<<<<<4 MAI<<TUANANH < < < < < < < < < < < < < < < < <"""

    # text_front2 = """CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM Độc lập - Tự do - Hạnh phúc SOCIALIST REPUBLIC OF VIET NAM Independence - Freedom - Happiness CĂN CƯỚC CÔNG DÂN Citizen Identity Card Số / No . : 079172016642 Họ và tên / Full name : NGUYỄN TUYẾT LAN Ngày sinh / Date of birth : 16/02/1972 197 Giới tính / Sex : Nữ Quốc tịch / Nationality : Việt Nam Quê quán / Place of origin : Phường 03 , Quận 3 , Thành phố Hồ Chí Minh Nơi thường trú / Place of residence : 101 . Phùng Tá Chu An Lạc Anh Tân , Thành phố Hồ Chí Minh Có giá trị đến : 16/02/2032 Date of expiry"""


    # Test extract ID
    # print("ID from front in back:", )

    # Test image extraction
    back = "./test/test_back1.jpeg"
    front = "./test/test1.jpeg"
    text1 = get_text_from_image(front)
    text2 = get_text_from_image(back)
    print("Front text:", extract_front_id(text1))
    print("Back text:", extract_back_id(text2))

