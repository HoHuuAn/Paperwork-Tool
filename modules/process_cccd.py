import cv2
import numpy as np
import os
from modules.CCCD import CCCD 

FRONT = cv2.imread('./assets/front.jpg', cv2.IMREAD_GRAYSCALE)
BACK = cv2.imread('./assets/back.jpg', cv2.IMREAD_GRAYSCALE)
MAX_NUM_FEATURES = 10000
ORB = cv2.ORB_create(MAX_NUM_FEATURES)
BFMATCHER = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


def process(path: str):

    side = detect_id_card_side(path)
    template = FRONT if side == "front" else BACK
    im1 = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)

    im2 = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    im2 = cv2.cvtColor(im2, cv2.COLOR_BGR2RGB)

    im1_gray = cv2.cvtColor(im1, cv2.COLOR_RGB2GRAY)
    im2_gray = cv2.cvtColor(im2, cv2.COLOR_RGB2GRAY)

    MAX_NUM_FEATURES = 10000
    orb = cv2.ORB_create(MAX_NUM_FEATURES)
    keypoints1, descriptors1 = orb.detectAndCompute(im1_gray, None)
    keypoints2, descriptors2 = orb.detectAndCompute(im2_gray, None)

    # im1_display = cv2.drawKeypoints(im1, keypoints1, outImage=np.array(
    #     []), color=(255, 0, 0), flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    # im2_display = cv2.drawKeypoints(im2, keypoints2, outImage=np.array(
    #     []), color=(255, 0, 0), flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    matcher = cv2.DescriptorMatcher_create(
        cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
    matches = matcher.match(descriptors1, descriptors2, None)

    matches = sorted(matches, key=lambda x: x.distance, reverse=False)

    numGoodMatches = int(len(matches) * 0.1)
    matches = matches[:numGoodMatches]

    points1 = np.zeros((len(matches), 2), dtype=np.float32)
    points2 = np.zeros((len(matches), 2), dtype=np.float32)

    for i, match in enumerate(matches):
        points1[i, :] = keypoints1[match.queryIdx].pt
        points2[i, :] = keypoints2[match.trainIdx].pt

    h, _ = cv2.findHomography(points2, points1, cv2.RANSAC)

    height, width, _ = im1.shape
    im2_reg = cv2.warpPerspective(im2, h, (width, height))

    file_name = os.path.splitext(os.path.basename(path))[0]
    directory = os.path.dirname(path)

    cv2.imwrite(directory + "/" + file_name + "_fix" + ".jpg", im2_reg)

    return CCCD(side=side, path=directory + "/" + file_name + "_fix" + ".jpg")


def detect_id_card_side(image_path):
    card_image = cv2.imread(image_path,  cv2.IMREAD_GRAYSCALE)

    des_card = ORB.detectAndCompute(card_image, None)[1]

    des_front = ORB.detectAndCompute(FRONT, None)[1]

    des_back = ORB.detectAndCompute(BACK, None)[1]

    similarity_front = get_similarity_from_desc(des_card, des_front)
    similarity_back = get_similarity_from_desc(des_card, des_back)

    return "front" if similarity_front > similarity_back else "back"


def get_similarity_from_desc(search, idx):
    matches = BFMATCHER.match(search, idx)
    distances = [m.distance for m in matches]
    distance = sum(distances) / len(distances)
    similarity = 1 / (1 + distance)
    return similarity
