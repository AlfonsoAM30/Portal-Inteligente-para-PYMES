from app.backend.product_design.segmentation import get_mask_v1
import cv2
import time

img = 'data/product.jpg'
inicio = time.time()
mask_v1, img_s = get_mask_v1(img)
cv2.imwrite('data/v1_seg/mask.png', img_s)

print(f'{time.time() - inicio}s')