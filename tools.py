import pyautogui as pa
from pynput import keyboard
import pyperclip as pc
import numpy as np
from PIL import ImageGrab
import cv2
import time


def getXY(img_model_path, threshold=0.1):
    # 读取模板图像
    template = cv2.imread(img_model_path)
    H,W,_ = template.shape

    # 截取整个屏幕
    screen = np.array(ImageGrab.grab())
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)  # PIL转OpenCV格式
    res = cv2.matchTemplate(screen, template, cv2.TM_SQDIFF_NORMED)
    # res = cv2.matchTemplate(img, img_model, cv2.TM_SQDIFF_NORMED)

    # 确定匹配位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if min_val <= threshold:
        # 计算中心坐标并返回
        x = int(min_loc[0] + W / 2)
        y = int(min_loc[1] + H / 2)
        return x,y,True
    else:
        return 0,0,False


# 目前这个阈值是我测试出来可以满足我的需求的
def getCloseXY(threshold=0.32):
    screen = np.array(ImageGrab.grab())
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    template = cv2.imread('data/close.png',0)

    # 进行边缘检测
    image_edges = cv2.Canny(screen, 50, 150)
    template_edges = cv2.Canny(template, 50, 150)

    # 进行模板匹配
    result = cv2.matchTemplate(image_edges, template_edges, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # 获取匹配结果的位置
    h, w = template.shape
    top_left = max_loc
    center = (top_left[0] + w // 2, top_left[1] + h // 2)

    # # 在原图上绘制矩形框
    # bottom_right = (top_left[0] + w, top_left[1] + h)
    # image_with_rect = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    # cv2.rectangle(image_with_rect, top_left, bottom_right, (0, 255, 0), 2)

    # # 显示结果
    # cv2.imshow('Result', image_with_rect)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # print(min_val,max_val)

    if max_val >= threshold:
        return center,True
    else:
        return (0,0),False


def keyClick(key, nums=1, interval=0.1):
    for i in range(nums):
        pa.keyDown(key)
        time.sleep(interval)
        pa.keyUp(key)


def clickStartToEnter(imgPath, maxWaitTime=10):
    startTime = time.time()
    bEnter = False

    while True:
        x,y,bClick = getXY(imgPath)
        if bClick:
            pa.click(x,y,duration=0.5,button='left')
            bEnter = True

        if bEnter and not bClick:
            return True
        if time.time() - startTime > maxWaitTime:
            print("超时退出：",imgPath)
            exit(-1)

        time.sleep(1)

def clickCloseForEnd(maxWaitTime=10):
    startTime = time.time()
    bEnter = False

    while True:
        (x,y),bClick = getCloseXY()
        if bClick:
            pa.click(x,y,duration=0.5,button='left')
            bEnter = True

        if bEnter and not bClick:
            return True
        if time.time() - startTime > maxWaitTime:
            print("超时,无法关闭")
            return False

        time.sleep(1.5)


def findSign(imgPath, point_list=[], maxWaitTime=10, interval=0.5):
    startTime = time.time()

    while True:
        x,y,bClick = getXY(imgPath)
        if bClick:
            point_list.extend([x,y])
            return True

        if time.time() - startTime > maxWaitTime:
            return False

        time.sleep(interval)

def getGame():
    pa.press('win')
    pc.copy("雷电模拟器")
    pa.hotkey('ctrl','v')
    time.sleep(0.5)
    pa.press('enter')


# 鼠标移动
def scroll(x1,y1,dis):
    pa.mouseDown(x1,y1)
    pa.move(dis,0,duration=0.5)
    pa.mouseUp()

# ================================= pvp ==========================================
gPvpRuning = True
def on_press(key):
    global gPvpRuning
    try:
        if key.char == 'q':
            pa.keyUp('k')
            pa.keyUp('space')
            exit(-1)
    except AttributeError:
        pass

def pvpKeyClick(key,nums=1,interval=0.1):
    global gPvpRuning
    if gPvpRuning:
        for i in range(nums):
            pa.keyDown(key)
            time.sleep(interval)
            pa.keyUp(key)
        return True
    else:
        pa.keyUp('k')
        pa.keyUp('space')
        return False

def detect_pvp_end():
    """子线程：持续按住 k 和 space，直到 PVP 结束"""
    # 创建键盘监听器
    # listener = keyboard.Listener(on_press=on_press)
    # listener.start()

    global gPvpRuning
    try:
        pa.keyDown('k')
        pa.keyDown('space')
        while gPvpRuning:  # 只要PVP还在运行，就保持按住
            # 实时识别pvp退出
            template = cv2.imread('data/jdcPvpEnd.png')
            x, y, w, h = (1549,56,247,119)
            screen = np.array(ImageGrab.grab(bbox=(x, y, x + w, y + h)))
            screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)  # PIL转OpenCV格式
            res = cv2.matchTemplate(screen, template, cv2.TM_SQDIFF_NORMED)

            # 确定匹配位置
            min_val, _, _, _ = cv2.minMaxLoc(res)
            if min_val <= 0.1:
                gPvpRuning = False
                break
            time.sleep(0.1)  # 短暂检测，避免卡死
    finally:
        pa.keyUp('k')  # PVP结束时释放按键
        pa.keyUp('space')
        print("pvp结束")
