import cv2
import numpy as np
import base64


def base64_to_image(base64_string: str):
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    img_bytes = base64.b64decode(base64_string)
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    img       = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    return img


def preprocess_image(img):
    if img is None:
        raise ValueError("Invalid image")

    avg_brightness = int(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).mean())
    print(f"Average brightness: {avg_brightness}")

    # Resize 2x
    img = cv2.resize(img, None, fx=2, fy=2,
                     interpolation=cv2.INTER_CUBIC)

    # Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Adaptive brightness — only boost if actually dark
    if avg_brightness < 80:
        gray = cv2.convertScaleAbs(gray, alpha=1.6, beta=30)
        print("Applied: heavy brightness boost")
    elif avg_brightness < 130:
        gray = cv2.convertScaleAbs(gray, alpha=1.2, beta=15)
        print("Applied: light brightness boost")
    else:
        gray = cv2.convertScaleAbs(gray, alpha=1.0, beta=0)
        print("Applied: no brightness change")

    # CLAHE for local contrast
    clahe    = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(gray)

    # Mild denoise
    denoised = cv2.fastNlMeansDenoising(contrast, h=8)

    # Mild sharpen — enough to crisp text edges
    kernel    = np.array([[0, -1,  0],
                          [-1, 5, -1],
                          [0, -1,  0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)

    # NO binary threshold — it destroys the image
    # Return grayscale with good contrast
    return sharpened