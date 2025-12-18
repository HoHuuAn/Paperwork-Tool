import cv2
import numpy as np
import os
import logging
from modules.CCCD import CCCD
from modules.google_lens import get_text_from_image, extract_back_id, extract_front_id, extract_id_number
# USE FOR VERSION 3

logger = logging.getLogger(__name__)

FRONT = cv2.imread('./assets/front.jpg', cv2.IMREAD_GRAYSCALE)
BACK = cv2.imread('./assets/back.jpg', cv2.IMREAD_GRAYSCALE)
FRONT_1 = cv2.imread('./assets/front_1.jpg', cv2.IMREAD_GRAYSCALE)
BACK_1 = cv2.imread('./assets/back_3.jpg', cv2.IMREAD_GRAYSCALE)
MAX_NUM_FEATURES = 10000
ORB = cv2.ORB_create(MAX_NUM_FEATURES)
BFMATCHER = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)


def process(path: str) -> CCCD | None:
    # 1. Chọn template theo loại mặt
    id = ""
    text = get_text_from_image(path)
    side = detect_id_card_side(path)
    id  = extract_id_number(text)
    # logger.debug(f"Path: {os.path.basename(path)}")
    # logger.debug(f"Side detected: {side}")
    # logger.debug(f"ID extracted: '{id}'")
    if side == "front_1":
        template = FRONT_1
        # id = extract_front_id(text)
    elif side == "back_1":
        template = BACK_1
        # id = extract_back_id(text)
    elif side == "front":
        template = FRONT
        # id = extract_front_id(text)
    else:
        template = BACK
        # id = extract_back_id(text)

    im1 = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
    im2 = cv2.imread(path, cv2.IMREAD_COLOR)

    # 2. Convert grayscale
    im1_gray = cv2.cvtColor(im1, cv2.COLOR_RGB2GRAY)
    im2_gray = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)

    # 3. Dùng SIFT
    sift = cv2.SIFT_create(MAX_NUM_FEATURES)
    keypoints1, descriptors1 = sift.detectAndCompute(im1_gray, None)
    keypoints2, descriptors2 = sift.detectAndCompute(im2_gray, None)

    if descriptors1 is None or descriptors2 is None:
        logger.error(f"Không tìm thấy đặc trưng nào: {path}")
        return CCCD("front" if (side == "front" or side == "front_1")
                  else "back", path=path, id=id, processed=False)

    # 4. FLANN matcher cho float descriptors
    index_params = dict(algorithm=1, trees=5)   # KD-Tree
    search_params = dict(checks=50)
    matcher = cv2.FlannBasedMatcher(index_params, search_params)

    matches = matcher.knnMatch(descriptors1, descriptors2, k=2)

    # 5. Lowe’s ratio test
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    if len(good_matches) < 4:
        print("Không đủ match tốt để tìm Homography")
        return CCCD("front" if (side == "front" or side == "front_1")
                  else "back", path=path, id=id, processed=False)

    # 6. Lấy toạ độ điểm
    points1 = np.float32(
        [keypoints1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    points2 = np.float32(
        [keypoints2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    # 7. Tính homography với RANSAC
    h, mask = cv2.findHomography(points2, points1, cv2.RANSAC, 5.0)

    if h is None or mask.sum() < 10:
        print("Homography không đáng tin cậy")
        return CCCD("front" if (side == "front" or side == "front_1")
                  else "back", path=path, id=id, processed=False)

    # 8. Warp ảnh theo homography
    height, width, _ = im1.shape
    im2_reg = cv2.warpPerspective(im2, h, (width, height))

    # 9. Lưu kết quả
    file_name = os.path.splitext(os.path.basename(path))[0]
    directory = os.path.dirname(path)
    out_path = os.path.join(directory, f"{file_name}_fix.jpg")

    cv2.imwrite(out_path, im2_reg)

    # 10. Gọi module CCCD
    result = CCCD("front" if (side == "front" or side == "front_1")
                  else "back", path=out_path, id=id, processed=True)
    return result


def detect_id_card_side(image_path):
    card_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    kp_card, des_card = ORB.detectAndCompute(card_image, None)

    kp_front, des_front = ORB.detectAndCompute(FRONT, None)
    kp_back, des_back = ORB.detectAndCompute(BACK, None)
    kp_front1, des_front1 = ORB.detectAndCompute(FRONT_1, None)
    kp_back1, des_back1 = ORB.detectAndCompute(BACK_1, None)

    similarity_scores = {
        "front": get_similarity_from_desc(kp_card, des_card, kp_front, des_front),
        "back": get_similarity_from_desc(kp_card, des_card, kp_back, des_back),
        "front_1": get_similarity_from_desc(kp_card, des_card, kp_front1, des_front1),
        "back_1": get_similarity_from_desc(kp_card, des_card, kp_back1, des_back1)
    }

    best = max(similarity_scores, key=similarity_scores.get)
    return best


def get_similarity_from_desc(kp1, des1, kp2, des2):
    if des1 is None or des2 is None:
        return 0

    # BFMatcher + knnMatch
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(des1, des2, k=2)

    # Lowe’s ratio test
    good = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good.append(m)

    if len(good) < 4:
        return 0

    # Lấy tọa độ điểm từ match
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    # RANSAC
    _, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    if mask is None:
        return 0

    inliers = mask.ravel().sum()
    similarity = float(inliers) / len(good)  # tỉ lệ inliers
    return similarity
