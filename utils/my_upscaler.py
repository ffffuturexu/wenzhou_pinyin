import numpy as np
import cv2
import math
from utils.config import *

def pixelMapping(img, scale):
    pixelX = 0
    pixelY = 0
    resizedHeight = height * scale
    resizedWidth = width * scale
    resized = np.zeros((resizedHeight, resizedWidth, 3), np.uint8)

    for x in range(resizedWidth):
        for y in range(resizedHeight):
            if pixelX * scale == x and pixelY * scale == y:
                resized[y, x] = img[pixelY, pixelX]
                pixelY += 1
                black = False
            else:
                if y == 0:
                    black = True
                    break
                resized[y, x] = [0, 0, 0]
        if not black:
            pixelX += 1
        pixelY = 0
    return resized

def bilinearInterpolation(img, step):
    x1 = 0
    x2 = step
    left = img[0,0]
    lb,lg,lr = left

    right = img[0, x2]
    rb,rg,rr = right

    height, width, _ = img.shape

    # Interpolate rows
    for y in range(height):
        if y % step == 0:
            for x in range(1, width):
                if x % step != 0:
                    b = ((x2 - x) / (x2 - x1)) * lb
                    g = ((x2 - x) / (x2 - x1)) * lg
                    r = ((x2 - x) / (x2 - x1)) * lr

                    b += ((x - x1) / (x2 - x1)) * rb
                    g += ((x - x1) / (x2 - x1)) * rg
                    r += ((x - x1) / (x2 - x1)) * rr

                    img[y, x] = [b, g, r]
                else:
                    x1 = x2
                    x2 += step
                    if x2 == width:
                        break

                    left = img[y, x]
                    lb,lg,lr = left

                    right = img[y, x2]
                    rb,rg,rr = right
        x1 = 0
        x2 = step

    left = img[0,0]
    lb,lg,lr = left

    right = img[x2, 0]
    rb,rg,rr = right

    #Interpolate columns
    for x in range(width):
        for y in range(1,height):
            if y % step != 0:
                b = ((x2 - y) / (x2 - x1)) * lb
                g = ((x2 - y) / (x2 - x1)) * lg
                r = ((x2 - y) / (x2 - x1)) * lr

                b += ((y - x1) / (x2 - x1)) * rb
                g += ((y - x1) / (x2 - x1)) * rg
                r += ((y - x1) / (x2 - x1)) * rr

                img[y, x] = [b, g, r]
            else:
                x1 = x2
                x2 += step
                if x2 == height:
                    break

                left = img[y, x]
                lb,lg,lr = left

                right = img[x2, x]
                rb,rg,rr = right
        x1 = 0
        x2 = step

    return img
    
def nearestNeighboor(img, scale):
    height, width, _ = img.shape
    resizedHeight = height * scale
    resizedWidth = width * scale
    resized = np.zeros((resizedHeight, resizedWidth, 3), np.uint8)

    RatioCol = height / resizedHeight
    RatioRow = width / resizedWidth

    for x in range(resizedWidth):
        for y in range(resizedHeight):
            resized[y,x] = img[math.ceil((y+1) * RatioCol) - 1, math.ceil((x+1) * RatioRow) - 1]
    return resized

def upscale(path, scale, technique="nearest"):
    # img = cv2.imread(imageName)
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), 1)
    # print("Image: ", img)
    if technique == "nearest":
        resized = nearestNeighboor(img, scale)
    elif technique == "bilinear":
        resized = pixelMapping(img, scale)
        resized = bilinearInterpolation(resized, scale)
    
    # cv2.imwrite("new" + imageName, resized)
    newpath = f'{pinyin_img_upscaled_path}{path.split("/")[1].split(".")[0]}_upscaled.png'
    cv2.imencode('.png', resized)[1].tofile(newpath)
    return newpath

# def main():
    
#     if args.technique == "nearest":
#         resized = nearestNeighboor(img, args.scale)

#     elif args.technique == "bilinear":
#         resized = pixelMapping(img, args.scale)
#         resized = bilinearInterpolation(resized, args.scale)

#     cv2.imwrite("new" + args.imageName, resized)

#     #===================================================================#
#     # Comment imwrite ^^^ and uncomment the below lines for live preview 
#     #===================================================================#

#     # cv2.namedWindow("image", cv2.WINDOW_NORMAL)
#     # cv2.imshow("image", resized)
#     # cv2.waitKey(0)
#     # cv2.destroyAllWindows()

if __name__ == "__main__":
    pass
