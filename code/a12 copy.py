import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math
import time
import multiprocessing as mp

d = -0.1  # 精度
sheet = list([])
times = 0
length = 0


def unit(v):  # 单位化
    return(v/np.linalg.norm(v))


def angle(v):  # 取辐角
    return(math.atan2(v[1], v[0]))


def inangle(v1, v2):  # 向量夹角
    return(math.acos(round(np.dot(v1, np.transpose(v2)) / (np.linalg.norm(v1)*np.linalg.norm(v2)), 9)))


def draw(data):  # 画线
    data = np.insert(data, data.shape[0], values=data[1, :], axis=0)
    data = np.insert(data, 0, values=data[data.shape[0]-3, :], axis=0)
    temp = np.array([0, 0])
    i = 0
    while i < data.shape[0]-2:
        v1 = data[i+1, :]-data[i, :]
        v2 = data[i+2, :]-data[i+1, :]
        if 0 < inangle(v1, v2) < math.pi*0.9:  # 一般情况在菱形中使用向量得到内缩点
            u = d/(math.sin(inangle(v1, v2)))
            if (angle(v2) > angle(v1) and not(angle(v2) > math.pi/2 and angle(v1) < -math.pi/2)) or (angle(v2) < -math.pi/2 and angle(v1) > math.pi/2):
                new = data[i+1, :]+(unit(v2)-unit(v1))*u
            else:
                new = data[i+1, :]-(unit(v2)-unit(v1))*u
        else:
            if inangle(v1, v2) == 0:  # 两向量平行的特殊情况
                if angle(v1) > 0:
                    new = data[i+1, :] + unit([v1[1], -v1[0]])*abs(d)
                else:
                    new = data[i+1, :] - unit([-v1[1], v1[0]])*abs(d)
            else:  # 排除转角过大的点
                i += 1
                continue
        i += 1
        temp = np.row_stack((temp, new))
    temp = np.delete(temp, 0, axis=0)
    temp = iflong(temp)  # 同级点间距控制
    temp = ifcross(temp)  # 交叉控制
    temp = district(temp, data)  # 与上一级间距控制
    plt.plot(temp[:, 0], temp[:, 1], '-', color='r')
    return(temp)


def iflong(data):  # 同级点间距控制
    i = 0
    while i < data.shape[0]-1:  # 遍历所有数据
        if np.linalg.norm(data[i+1, :]-data[i, :]) > 2*abs(d):  # 两点间距过大的添加中点
            new = np.array([(data[i+1, 0]+data[i, 0])/2,
                            (data[i+1, 1]+data[i, 1])/2])
            data = np.insert(data, i+1, new,  axis=0)
            continue
        else:
            i = i+1
    return(data)


def district(data, last):
    global sheet
    q = mp.Queue()
    jobs = []
    sheet = list([])
    max = mp.cpu_count()
    if data.shape[0] / max < 300:
        max = int(data.shape[0]/300)
    n = int(data.shape[0]/max)
    for i in range(max-1):
        sheet.append(data[n*i:n*(i+1)])
        p = mp.Process(target=ifwide, args=(sheet[i], last, q))
        jobs.append(p)
        p.start()
    sheet.append(data[n*(max-1):data.shape[0]])
    p = mp.Process(target=ifwide, args=(sheet[max-1], last, q))
    jobs.append(p)
    p.start()
    for p in jobs:
        p.join()
    output = [q.get() for j in jobs]
    return(output)


def ifwide(data, last, q):  # 与上一级间距控制
    i = 0
    while i < data.shape[0]:  # 遍历该级所有数据
        j = 0
        while j < last.shape[0]:  # 遍历上级所有数据
            if i >= data.shape[0]:
                break
            if np.linalg.norm(data[i, :]-last[j, :]) < abs(d)*0.999:  # 小于一个精度的直接删除
                data = np.delete(data, i, axis=0)
                if j > 20:
                    j -= 20
                else:
                    j = 0
            else:
                j += 1
        i += 1
    q.put(data)


def ifcross(data):  # 交叉控制
    i = 0
    while i < data.shape[0]-3:  # 遍历该级所有数据
        v1 = data[i+1, :]-data[i, :]
        v2 = data[i+2, :]-data[i+1, :]
        v3 = data[i+3, :]-data[i+2, :]
        if inangle(v1, v2)+inangle(v2, v3) > math.pi:  # 连续三个向量转角超过180度直接删除
            data = np.delete(data, [i+1, i+2], axis=0)
        else:
            i += 1
    return(data)


def ifdivide(data):  # 判断区域划分
    for i in range(data.shape[0]-2):
        for j in range(i, data.shape[0]-2):
            x1 = data[i, 0]
            y1 = data[i, 1]
            x2 = data[j, 0]
            y2 = data[j, 1]
            if 0 < math.sqrt((x2-x1)**2+(y2-y1)**2) < abs(d) and j-i > 3:  # 间距过近且向量方向差超过90度
                v1 = data[i+2, :]-data[i, :]
                v2 = data[j+2, :]-data[j, :]
                if abs(angle(v1)-angle(v2)) > math.pi/2:
                    return(np.array([i, j]))
    return(np.array([0, 0]))


def drawline(data):
    print('+')
    global times
    while True:
        temp = data
        if data.shape[0] < 10:
            print('-')
            break
        index = ifdivide(temp)  # 分割点序号
        if index[0] == 0 and index[1] == 0:
            data = draw(temp)
            times += 1
            print(times)
            # plt.plot(data0[:, 0], data0[:, 1], '-o', color='b', markersize=1)
            # plt.show()
            # plt.axis("equal")
        else:
            new = temp[math.floor(index[0])+1: math.floor(index[1]), :]
            new = np.row_stack((new, new[0, :]))
            mp.Process(target=drawline, args=(new,)).start()
            temp1 = temp[0:math.floor(index[0])+1, :]
            temp2 = temp[math.floor(index[1]):temp.shape[0], :]
            data = np.row_stack((temp1, temp2))
    pass


if __name__ == '__main__':
    start = time.thread_time()

    data0 = np.array(pd.read_csv(".\code\graph1.csv", header=2))
    data = data0  # 从csv文件获取数据
    plt.axis("equal")
    plt.plot(data[:, 0], data[:, 1], '-o', markersize=1)

    q = mp.Queue()
    jobs = []
    data = drawline(data)

    end = time.thread_time()
    print('Length of curve: %s mm' % length)
    print('Number of turns: %s' % times)
    print('Running time:    %s Seconds' % (end-start))

    plt.show()
