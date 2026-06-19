import os

from modules.CCCD import CCCD


def get_normalized_id(image: CCCD) -> str:
    image_id = image.get_id()
    return image_id.strip() if image_id else ""


def get_image_label(image: CCCD) -> str:
    image_id = get_normalized_id(image) or "khong doc duoc ID"
    return f"{image_id} ({os.path.basename(image.get_path())})"


def build_image_pairs(processed_images: list[CCCD]):
    groups = {}
    error_images = []

    for order, img in enumerate(processed_images):
        if img is None:
            continue

        img_id = get_normalized_id(img)
        if img_id not in groups:
            groups[img_id] = {
                "first_order": order,
                "front": [],
                "back": [],
                "unknown": [],
            }

        if not getattr(img, 'processed', True):
            error_images.append(get_image_label(img))
            continue

        side = img.get_side()
        if side == 'front':
            groups[img_id]["front"].append((order, img))
        elif side == 'back':
            groups[img_id]["back"].append((order, img))
        else:
            groups[img_id]["unknown"].append((order, img))

    image_pairs = []
    unpaired_groups = []

    for img_id, group in sorted(groups.items(), key=lambda item: item[1]["first_order"]):
        fronts = sorted(group["front"], key=lambda item: item[0])
        backs = sorted(group["back"], key=lambda item: item[0])
        pair_count = min(len(fronts), len(backs))

        for index in range(pair_count):
            image_pairs.append([fronts[index][1], backs[index][1]])

        if len(fronts) != len(backs) or group["unknown"]:
            display_id = img_id or "khong doc duoc ID"
            unpaired_groups.append(
                f"{display_id} (front: {len(fronts)}, back: {len(backs)}, unknown: {len(group['unknown'])})"
            )

    return image_pairs, error_images, unpaired_groups
