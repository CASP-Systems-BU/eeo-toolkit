import os
import shutil

import cv2
import fitz
import imutils
import numpy as np

from logger.logger import Logger

input_dir = "/home/node3/Documents/data/eolwd-raw_data/On-Time Filings/valid_submissions/EEO1/scanned"
logs_dir = f"{input_dir}/logs"
os.makedirs((logs_dir), exist_ok=True)

output_dir = f"{input_dir}/rotated"
os.makedirs((output_dir), exist_ok=True)

# Moved done files to folder
done_dir = os.path.join(input_dir, "done")
os.makedirs((done_dir), exist_ok=True)

SCALE_FACTOR = 2

def read_pdf_as_image(pdf_path, page_number=0):
    doc = fitz.open(pdf_path)

    if page_number >= len(doc):
        raise ValueError(
            f"Invalid page number {page_number}. PDF has {len(doc)} pages."
        )

    page = doc[page_number]

    matrix = fitz.Matrix(SCALE_FACTOR, SCALE_FACTOR)
    pix = page.get_pixmap(matrix=matrix)

    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n
    )
    #
    # if pix.n == 4:  # RGBA → RGB
    #     img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    # if pix.n >= 3:  # RGB → Grayscale
    #     img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    doc.close()
    return img


def get_contours_from_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    threshold = cv2.adaptiveThreshold(gray.copy(), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 301, 11)
    keypoints = cv2.findContours(threshold.copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(keypoints)
    return contours


def get_files_in_directory(directory, extension=".pdf"):
    if not os.path.exists(directory):
        raise FileNotFoundError(f"The directory {directory} does not exist.")
    return [f for f in os.listdir(directory) if f.lower().endswith(extension)]


def get_closest_angle(angle, a1, a2):
    return a1 if abs(angle - a1) < abs(angle - a2) else a2


def figure_out_rotation_dir(box_points, angle):
    box_points = cyclic_points(box_points)
    file_logger.info(f"OG Angle: {angle}")
    tl, tr, br, bl = box_points

    tlx = tl[0]
    tly = tl[1]

    blx = bl[0]
    bly = bl[1]

    trx = tr[0]
    tryy = tr[1]

    brx = br[0]
    bry = br[1]

    # angle = int(angle)

    if angle == 90.0 or angle == 0.0:
        file_logger.info(f"Angle is 90 or 0, no need to rotate: {angle}")
        return 0

    if tly < tryy and bly < bry:
        if get_closest_angle(angle, 0, 90) == 0:
            file_logger.info(f"Needs to be rotated counter-clockwise: {angle}")
        elif get_closest_angle(angle, 0, 90) == 90:
            angle = 90 - angle
            file_logger.info(f"Needs to be rotated counter-clockwise: {angle}")
        else:
            file_logger.info(f"Needs to be rotated counter-clockwise. not sure of angle: {angle}")

    elif tly > tryy and bly > bry:
        if get_closest_angle(angle, 0, 90) == 0:
            angle = -1 * angle
            file_logger.info(f"Needs to be rotated clockwise: {angle}")
        elif get_closest_angle(angle, 0, 90) == 90:
            angle = -1 * (90 - angle)
            file_logger.info(f"Needs to be rotated clockwise: {angle}")
        else:
            file_logger.info(f"Needs to be rotated clockwise. not sure of angle: {angle}")

    return angle


def cyclic_points(pts):
    if pts.shape[0] != 4:
        return None
    center = np.mean(pts, axis=0)
    cyclic_points = [
        # Top left
        pts[np.where(np.logical_and(pts[:, 0] < center[0], pts[:, 1] < center[1]))[0][0], :],

        # Top right
        pts[np.where(np.logical_and(pts[:, 0] > center[0], pts[:, 1] < center[1]))[0][0], :],

        # Bottom right
        pts[np.where(np.logical_and(pts[:, 0] > center[0], pts[:, 1] > center[1]))[0][0], :],

        # Bottom left
        pts[np.where(np.logical_and(pts[:, 0] < center[0], pts[:, 1] > center[1]))[0][0], :]
    ]

    return (cyclic_points)


def get_min_rect_and_box_points(contour):
    minRect = cv2.minAreaRect(contour)
    boxPoints = cv2.boxPoints(minRect)
    boxPoints = np.intp(boxPoints)
    return minRect, boxPoints


def utils_rotate_bound(image, angle):
    # grab the dimensions of the image and then determine the
    # center
    (h, w) = image.shape[:2]
    (cX, cY) = (w / 2, h / 2)

    # grab the rotation matrix (applying the negative of the
    # angle to rotate clockwise), then grab the sine and cosine
    # (i.e., the rotation components of the matrix)
    M = cv2.getRotationMatrix2D((cX, cY), angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])

    # compute the new bounding dimensions of the image
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))

    # adjust the rotation matrix to take into account translation
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY

    # perform the actual rotation and return the image
    return cv2.warpAffine(image, M, (nW, nH), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))


def rotational_transform(img, contour):
    minRect, boxPoints = get_min_rect_and_box_points(contour)
    (x, y), (w, h), angle = minRect
    #
    angle = figure_out_rotation_dir(boxPoints, angle)
    rotated_image = utils_rotate_bound(img, angle)

    # M = cv2.getRotationMatrix2D((x, y), angle, 1.0)
    # rotated_image = cv2.warpAffine(img, M, (int(w), int(h)))
    return rotated_image


def perspective_transform(img, largest_contour):
    minRect, boxPoints = get_min_rect_and_box_points(largest_contour)
    boxPoints = np.array(cyclic_points(boxPoints))
    file_logger.info(f"Box points are: {boxPoints}")

    (x, y), (width, height), angle = minRect
    dstPoints = [[0, 0], [width, 0], [width, height], [0, height]]

    M = cv2.getPerspectiveTransform(np.float32(boxPoints), np.float32(dstPoints))
    transformed_image = cv2.warpPerspective(img, M, (int(width), int(height)))

    return transformed_image, boxPoints


def get_image_within_contour(img, contour):
    x, y, w, h = cv2.boundingRect(contour)
    cropped_image = img[y:y + h, x:x + w]
    return cropped_image


def clean_sharpen_image(page_image):
    img = page_image.copy()
    # Sharpening image
    sharpen_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened_image = cv2.filter2D(img, -1, sharpen_kernel)

    hsv = cv2.cvtColor(sharpened_image.copy(), cv2.COLOR_BGR2HSV)
    mask_grey = cv2.inRange(hsv, (0, 0, 100), (255, 5, 255))
    nzmask = cv2.inRange(hsv, (0, 0, 5), (255, 255, 255))
    nzmask = cv2.erode(nzmask, np.ones((3, 3)))
    mask_grey = mask_grey & nzmask

    cleaned_bg_image = img.copy()
    cleaned_bg_image[np.where(mask_grey)] = 255

    cleaned_bg_image = cv2.cvtColor(cleaned_bg_image.copy(), cv2.COLOR_BGR2RGB)
    return cleaned_bg_image
    # gray = cv2.cvtColor(cleaned_bg_image, cv2.COLOR_BGR2GRAY)
    # return gray

    # return cl


def pixmap_insert_image_page_to_doc(doc, image):
    h, w, channels = image.shape
    # print(f"Shape value: {image.shape}")
    image_page = doc.new_page(width=w, height=h)

    # Image byte encoding
    _, buffer = cv2.imencode(".jpg", image)

    rotated_image_pixmap = fitz.Pixmap(buffer.tobytes())

    image_page.insert_image(image_page.rect, pixmap=rotated_image_pixmap)


def core_process(pdf_path, filename, output_folder, pdf_doc, new_doc):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for i, page in enumerate(pdf_doc):
        page_image = read_pdf_as_image(pdf_path, i)
        clean_sharp_image = clean_sharpen_image(page_image)

        working_image = clean_sharp_image.copy()
        contours = get_contours_from_image(working_image)
        largest_contour = max(contours, key=cv2.contourArea)
        # cv2.drawContours(working_image, [largest_contour], 0, (255, 0, 0), 2)
        # cv2.imshow("Largest contour", working_image)

        # Attempt rotation
        # transformed_image, box = perspective_transform(page_image.copy(), largest_contour)
        transformed_image = rotational_transform(page_image.copy(), largest_contour)
        # cv2.imshow("Rotated Image", transformed_image)

        # cropped_working_image = clean_sharpen_image(transformed_image)
        # transformed_contours = get_contours_from_image(cropped_working_image)
        # max_transformed_contour = max(transformed_contours, key=cv2.contourArea)
        # cv2.drawContours(cropped_working_image, [max_transformed_contour], 0, (0, 255, 0), 2)
        # cv2.imshow("Cropped transformed image", cropped_working_image)

        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        # Write rotated image to pdf
        pixmap_insert_image_page_to_doc(new_doc, transformed_image)

    # Pages inserted, write to pdf file
    out_path = os.path.join(output_folder, f"{filename}_rotated.pdf")
    new_doc.save(out_path)
    file_logger.info(f"Rotated PDF saved to {out_path}")


if __name__ == "__main__":
    global file_logger

    pdf_files = get_files_in_directory(input_dir)
    for pdf_file in pdf_files:
        pdf_file_name, _ = os.path.splitext(pdf_file)
        file_logger = Logger(
            log_file_path=f"{logs_dir}/rotate_pages_{pdf_file_name}.log",
            prefix="ROTATE_PAGES",
        )
        file_logger.info(f"Processing {pdf_file}")

        pdf_path = f"{input_dir}/{pdf_file}"

        pdf_doc = fitz.open(pdf_path)
        new_doc = fitz.open()
        try:
            core_process(pdf_path, pdf_file_name, output_dir, pdf_doc, new_doc)
        except Exception as e:
            file_logger.warning(f"Exception processing {pdf_file}: {e}")

        pdf_doc.close()
        new_doc.close()

        shutil.move(pdf_path, os.path.join(done_dir, pdf_file))
