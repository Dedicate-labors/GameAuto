import pyautogui as pa
from pynput import keyboard
import time
from datetime import datetime
from tools import *
import threading


# 有开启失败的风险！！
def step1_enter_game():
    getGame()
    time.sleep(8)
    print('打开游戏')
    clickStartToEnter('data/GameIcon.png',30)
    time.sleep(28)
    print('点击开始')
    clickStartToEnter('data/GameStart.png',60)
    time.sleep(28)

def step2_disable_startup_ads():
    print('关闭开机广告,可能没有')
    clickCloseForEnd()
    # for i in range(3):
    #     center,bClick = getCloseXY()
    #     if bClick:
    #         pa.click(center[0],center[1],duration=0.5,button='left')
    #         time.sleep(2)
    print('领取登录奖励')
    if clickStartToEnter('data/loginReward.png'):
        time.sleep(6)
    print('关闭活动广告,可能没有')
    clickCloseForEnd()
    time.sleep(4)
    # for i in range(3):
    #     center,bClick = getCloseXY()
    #     if bClick:
    #         pa.click(center[0],center[1],duration=0.5,button='left')
    #         time.sleep(2)

def step3_dungeon_sweep():
    print('进行副本扫荡')
    pointTmp = []
    if findSign('data/fbsdEnter1.png', pointTmp):
        pa.click(pointTmp[0],pointTmp[1],duration=0.5,button='left')
    pointTmp = []
    if findSign('data/fbsdEnter2.png', pointTmp):
        pa.click(pointTmp[0],pointTmp[1],duration=0.5,button='left')

    # 固定偏移
    startoffset = (-50, 93)
    moveoffset = 114
    returnX, retrunY, closeoffset = 0, 0, 125

    # 这里比较绕，可能要重写
    point_list = []
    if findSign('data/fbsdSign1.png', point_list):
        x, y = point_list
        startX = x + startoffset[0]
        startY = y + startoffset[1]
        pa.moveTo(startX,startY,duration=0.5)
        # 6 个可刷镶嵌饰品
        for index in range(6):
            pa.click()
            time.sleep(0.5)
            point_list1 = []
            point_list2 = []
            point_list3 = []
            if findSign('data/fbsdStart.png', point_list1, maxWaitTime=2):
                x1, y1 = point_list1
                returnX, retrunY = x1, y1+closeoffset
                pa.click(x1,y1,duration=0.5,button='left')
                time.sleep(0.5)
                x,y,bClick = getXY('data/fbsdStart2.png')
                if bClick:
                    pa.click(x,y,duration=0.5,button='left',clicks=20,interval=1.8)
                break
            elif findSign('data/fbsdMerge.png', point_list2, maxWaitTime=2):
                x2, y2 = point_list2
                returnX, retrunY = x2, y2+closeoffset
                pa.click(returnX, retrunY, duration=0.5,button='left')
                time.sleep(0.5)
            elif findSign('data/fbsdReturn1.png', point_list3, maxWaitTime=2):     
                returnX, retrunY = point_list3[0]-138, point_list3[1]
                pa.click(returnX, retrunY, duration=0.5,button='left')
                time.sleep(0.5)
            startX += moveoffset
            pa.moveTo(startX,startY,duration=0.8)

    pa.click(returnX, retrunY, clicks=2, interval=0.5)
    time.sleep(1.5)
    clickCloseForEnd()
    time.sleep(2)

# 这个可以用录制操作代替
def step4_daily_sharing():
    print('进行每日分享')
    if clickStartToEnter('data/userCenter.png'):
        time.sleep(2)
    if clickStartToEnter('data/share.png'):
        time.sleep(2)
    if clickStartToEnter('data/shareQQ.png'):
        time.sleep(2)
    point_list = []
    if findSign('data/phoneReturn.png', point_list):
        pa.click(point_list[0],point_list[1], duration=0.5, button='left')
        time.sleep(2)

# 这个可以用录制操作代替
def step5_chamber_of_abundance():
    print('进行丰饶之间')
    if clickStartToEnter('data/frzjGame.png'):
        time.sleep(1)
    if clickStartToEnter('data/frzjChallenge.png'):
        time.sleep(1)
    # 识别到计时开始
    if findSign('data/frzjStart.png'):
        keyClick('j',nums=2)
        time.sleep(0.8)
        keyClick('i',nums=2)
        time.sleep(1.5)
        keyClick('l')
        time.sleep(5)
    # 点击结束收获显示
    if clickStartToEnter('data/frzjEnd.png'):
        time.sleep(1)
        clickCloseForEnd()
        time.sleep(1.5)

def step6_team_raid():
    # 周一的时候需要勾选！！麻烦，暂时还未写
    # if datetime.now().weekday() == 0:
    #     print("不消耗金币")

    print('进行小队突袭x2')
    if clickStartToEnter('data/xdtxGame.png'):
        time.sleep(1)
    for i in range(2):
        point_challenge=[]
        if findSign('data/xdtxChallenge.png',point_challenge):
            pa.click(point_challenge[0],point_challenge[1],duration=0.5,button='left')
            time.sleep(10)
            if findSign('data/xdtxStart.png'):
                print("挑战开始", datetime.now())
                time.sleep(15)
            if clickStartToEnter('data/xdtxEnd.png', maxWaitTime=30):
                print("挑战结束", datetime.now())
            time.sleep(1.5)
    clickCloseForEnd()
    time.sleep(1.5)

# 脚本可以替换，但操作目标固定就是下面4个（脚本放置到最后运行）
def step7_run_operation_script():
    print('进行操作脚本: 每日祈福、金币招财、忍者招募、体力领取')
    point_game = []
    if findSign('data/operationGame1.png', point_game):
        pa.click(point_game[0],point_game[1],duration=0.5,button='left')
        time.sleep(0.8)
        point_game.clear()
        if findSign('data/operationGame2.png', point_game):
            pa.click(point_game[0],point_game[1],duration=0.5,button='left')
            time.sleep(0.8)
            point_game.clear()
            if findSign('data/operationGame3.png', point_game):
                pa.click(point_game[0],point_game[1],duration=0.5,button='left')

def pvp():
    print('进行pvp')
    if clickStartToEnter('data/jdcGame1.png'):
        time.sleep(0.8)
    if clickStartToEnter('data/jdcGame2.png'):
        time.sleep(0.8)

    # 至少6场
    for i in range(6):
        point_list = []
        if findSign('data/jdcStart.png', point_list):
            pa.click(point_list[0],point_list[1],duration=0.5,button='left',clicks=2,interval=0.8)
            print('pvp匹配等候中ing ......')
            time.sleep(9)
            point_list.clear()

        # pvp开始
        if findSign('data/jdcPvpStart.png', maxWaitTime=40, interval=1):
            print('pvp开始')

            detect_thread = threading.Thread(target=detect_pvp_end, daemon=True)
            detect_thread.start()

            while True:
                
                # 在每个按键点击之前识别下pvp是否结束
                if pvpKeyClick('m'):
                    time.sleep(0.4)
                else:
                    break

                if pvpKeyClick('i',nums=2):
                    time.sleep(1.4)
                else:
                    break

                if pvpKeyClick('j',nums=2):
                    time.sleep(2.7)
                else:
                    break

                if pvpKeyClick('n'):
                    # 技能这些不可能好那么快的
                    time.sleep(6)
                else:
                    break
        
        keyClick('k')
        time.sleep(0.5)
    
    clickCloseForEnd()
    time.sleep(1.5)

# 余下：奖励领取、【每日签到(看着点吧) + 后续可能的月卡】（暂不处理）

if __name__ == '__main__':
    # step1_enter_game()

    step2_disable_startup_ads()

    step3_dungeon_sweep()

    step4_daily_sharing()

    step5_chamber_of_abundance()

    step6_team_raid()

    # pvp()

    # step7_run_operation_script()

