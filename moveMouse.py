'''
鼠标移动+移动时间
鼠标偏移+移动时间
获取当前鼠标位置+屏幕分辨率
'''

import pyautogui as pa
from pynput import mouse
from pynput import keyboard
import pyperclip as pc
import time
from tools import *

# 参数：x,y,duration-单位是秒
# 2s是移动时间
# x,y坐标范围是0-1919,0-1079
# pa.moveTo(100,100,2)

# 鼠标偏移和移动时间
# 也不能超出范围的偏移以及是0,0
# pa.move(100,100)

# 获取当前鼠标位置+屏幕分辨率
# print(pa.position(),pa.size())

# 实时获取当前鼠标位置 和 相对像素偏移值
# x0, y0 = pa.position()
# x0,y0,bClick = getXY('data/fbsdReturn1.png')
# print("起点坐标：",x0,y0)
# def on_click(x, y, button, pressed):
#     if button == mouse.Button.left and pressed:
#         # 计算点击坐标相对于坐标 A 的 x、y 像素偏移
#         offset_x = x - x0
#         offset_y = y - y0
#         print(f"点击坐标相对于坐标 A 的 (x,y) 像素偏移为: {offset_x} {offset_y}")
#     if button == mouse.Button.right and pressed:
#         # 停止监听
#         return False


# # 开始监听鼠标事件
# with mouse.Listener(on_click=on_click) as listener:
#     listener.join()
        

# 鼠标点击(默认左键单击)
# pa.moveTo(132,563)
# time.sleep(1)
# 参数：x,y坐标
# pa.click(132,563,duration=1)

# 鼠标的按下
# pa.moveTo(132,563,1)
# pa.mouseDown()
# time.sleep (2)
# pa.mouseUp()

# 鼠标滑轮
# 参数：滚动的距离 正数向上，负数向下
# 1000的值大概滑动8次 -- 电脑设置里有“一次滚动的行数”
# pa.scroll(100)

# 定义一个全局变量来控制循环
is_running = True

def on_press(key):
    global is_running
    try:
        if key.char == 'q':
            is_running = False
            pa.keyUp('k')
            pa.keyUp('space')
            print('pvp结束')
    except AttributeError:
        pass

# 创建键盘监听器
listener = keyboard.Listener(on_press=on_press)
listener.start()

# pvp开始
if findSign('data/jdcPvpStart.png'):
    print('pvp开始')
    # 按下普工和替身不松手
    pa.keyDown('k')
    # pa.keyDown('space')
    while is_running:
        # pvp 总截图
        pa.screenshot('data/pvpScreenshot.png')
        pvpImg = cv2.imread('data/pvpScreenshot.png')
        
        keyClick('m')
        time.sleep(0.4)
        keyClick('i')
        time.sleep(1.4)
        keyClick('j')
        time.sleep(2.7)
        keyClick('n')

        # 识别是否可以退出pvp
        img_pvpend = cv2.imread('data/jdcPvpEnd.png')
        H,W,_ = img_pvpend.shape
        res = cv2.matchTemplate(pvpImg, img_pvpend, cv2.TM_SQDIFF_NORMED)
        # 确定匹配位置
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if min_val <= 0.1:
            # 计算中心坐标
            x = int(min_loc[0] + W / 2)
            y = int(min_loc[1] + H / 2)
            pa.keyUp('k')
            pa.keyUp('space')
            print('pvp结束')
            pa.click(x,y,duration=0.5,button='left')
            time.sleep(1.5)
            break


        # 技能这些不可能好那么快的
        time.sleep(6)

