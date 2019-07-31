# -*- coding: utf-8 -*-

import Map
import paho.mqtt.client as mqtt
import requests
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap
import sys
import os
import threading
from PIL import Image
import ctypes
import inspect
import time

MQTTHOST = "139.199.208.33"
MQTTPORT = 1883
USERNAME = ""
PASSWORD = ""
TOPIC = r'/CC3200@SHIP/2/SHIPDATA/SENSORDATA'
CLIENTID = "SXF_Python_GPSMap"
HEARTBEAT = 60
client = mqtt.Client(CLIENTID)
longitude_last = 0.0
latitude_last = 0.0
t_cnt = 0


class GPS_Data(object):
    def __init__(self):
        self.UTC_year = 0           # 年份
        self.UTC_mon = 0            # 月份
        self.UTC_day = 0            # 日期
        self.UTC_hor = 0            # 小时
        self.UTC_min = 0            # 分钟
        self.UTC_sec = 0.0          # 秒钟
        self.status = ''            # 定位状态: A, 有效定位; V, 无效定位
        self.latitude = 0.0         # 纬度
        self.lat_hemisphere = ''    # 纬度半球, N: 北纬; S: 南纬
        self.longitude = 0.0        # 经度
        self.lon_hemisphere = ''    # 经度半球, E: 东经; W: 西经
        self.speed = 0.0            # 地面速率, 单位: 1公里 / 小时
        self.course = 0.0           # 地面航向, 0~359.9°
        self.declination = 0.0      # 磁偏角, 0~180.0°
        self.declination_dir = ''   # 磁偏角方向, E, 东; W, 西
        self.mode = ''              # 模式指示, A自主定位;D查分;E估算; N数据无效


class MyMainWindow(Map.Ui_MainWindow):
    def __init__(self):
        self.thread_list = []
        self.label_debug_cnt = 0
        self.label_debug_string = ""
        self.gps_list_string = ""

    def setupUi(self, MainWindow):
        MainWindow.setFixedSize(1120, 710)  # 禁止最大化和调整窗口大小
        super(MyMainWindow, self).setupUi(MainWindow)

    def Start(self):
        self.Clear()
        self.Label_Debug(">> 启动中...")
        mqtt_thread = threading.Thread(target=self.mqtt)
        mqtt_thread.start()
        self.thread_list.append(mqtt_thread)

    def Stop(self):
        try:
            client.loop_stop()
            self.stop_thread(self.thread_list.pop())
            self.Label_Debug("终止成功!")
            print("终止成功!")
        except Exception as e:
            self.Label_Debug(str(e))
            print(e)

    def Reset(self):
        self.label_status.setText("A有效;V无效")
        self.label_mode.setText("A自主;D差分;E估算; N无效")
        self.label_time.setText("年/月/日 时:分:秒")
        self.label_lat.setText("N北纬;S南纬")
        self.label_lon.setText("E东经;W西经")
        self.label_speed.setText("公里/小时")
        self.label_course.setText("0~359.9°")
        self.label_declination.setText("0~180.0°")
        self.label_declination_dir.setText("E东;W西")
        self.label_debug.setText("DeBug Here")
        self.label_img.setText("GPS Map Here")
        self.lineEdit_topic_rec.setText("")
        self.label_roll_v.setText("")
        self.label_roll_dot.setText("")
        self.label_pitch_v.setText("")
        self.label_pitch_dot.setText("")
        self.label_yaw_v.setText("")
        self.label_yaw_dot.setText("")

    def Clear(self):
        self.label_debug_cnt = 13
        self.Label_Debug("")

    def Subs(self):
        global MQTTHOST, MQTTPORT, USERNAME, PASSWORD, TOPIC, CLIENTID, HEARTBEAT
        self.Clear()
        MQTTHOST = self.lineEdit_host.text()
        MQTTPORT = int(self.lineEdit_port.text() or 1883)
        USERNAME = self.lineEdit_username.text()
        PASSWORD = self.lineEdit_password.text()
        TOPIC = self.lineEdit_topic.text()
        CLIENTID = self.lineEdit_clientid.text()
        HEARTBEAT = int(self.lineEdit_heartbeat.text() or 60)
        self.pushButton_submit.setText("√")
        QApplication.processEvents()
        time.sleep(1)
        self.pushButton_submit.setText("Submit")
        self.Label_Debug("*"*60+">> 配置成功! <<\r\n"+"Host:%s\r\nPort:%s\r\nUsr:%s\r\nPwd:%s\r\nId:%s\r\nBeat:%s\r\nTopic:%s\r\n" % (
            MQTTHOST, MQTTPORT, USERNAME, PASSWORD, CLIENTID, HEARTBEAT, TOPIC
        ) + "*"*60)

    def Label_Debug(self, string):
        if self.label_debug_cnt == 13:
            self.label_debug_string = ""
            self.label_debug.setText(self.label_debug_string)
            self.label_debug_cnt = 0
        self.label_debug_string += string + "\r\n"
        self.label_debug.setText(self.label_debug_string)
        self.label_debug_cnt += 1

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        self.Label_Debug("Connected with result code " + str(rc))
        self.Label_Debug("订阅主题 -> %s" % TOPIC)
        client.subscribe(TOPIC)

    def on_message(self, client, userdata, msg):
        global t_cnt
        MQTT_Rx_Buff = str(msg.payload, encoding="utf-8")
        self.lineEdit_topic_rec.setText(msg.topic)
        self.GPS_Calculate(MQTT_Rx_Buff)
        self.MPU6050_Calculate(MQTT_Rx_Buff)
        t_cnt += 1
        if t_cnt > 2:
            t_cnt = 0
            self.gps_map_main(GPS_Data.longitude, GPS_Data.latitude)

    def mqtt(self):
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.username_pw_set(USERNAME, PASSWORD)
        client.connect(MQTTHOST, MQTTPORT, HEARTBEAT)
        # client.loop_forever()  # 阻塞
        client.loop_start()  # 线程

    def GPS_Calculate(self, GPS_Buff):
        if "$GNRMC" not in GPS_Buff:
            return
        GPS_Buff = GPS_Buff.split(',')
        GPS_Data.UTC_hor = int(GPS_Buff[1][0:2]) + 8
        GPS_Data.UTC_min = int(GPS_Buff[1][2:4])
        GPS_Data.UTC_sec = float(GPS_Buff[1][4:9])
        GPS_Data.status = GPS_Buff[2]
        GPS_Data.latitude = '%.6f' % (float(GPS_Buff[3][0:2]) + float(GPS_Buff[3][2:]) / 60)  # 度
        GPS_Data.lat_hemisphere = GPS_Buff[4]
        GPS_Data.longitude = '%.6f' % (float(GPS_Buff[5][0:3]) + float(GPS_Buff[5][3:]) / 60)  # 度
        GPS_Data.lon_hemisphere = GPS_Buff[6]
        GPS_Data.speed = GPS_Buff[7]
        GPS_Data.course = GPS_Buff[8]
        GPS_Data.UTC_year = GPS_Buff[9][4:]
        GPS_Data.UTC_mon = GPS_Buff[9][2:4]
        GPS_Data.UTC_day = GPS_Buff[9][0:2]
        GPS_Data.declination = GPS_Buff[10]
        GPS_Data.declination_dir = GPS_Buff[11]
        GPS_Data.mode = GPS_Buff[12][0]

        self.label_status.setText(GPS_Data.status)
        self.label_mode.setText(GPS_Data.mode)
        self.label_time.setText("%s/%s/%s %s:%s:%s" % (GPS_Data.UTC_year,GPS_Data.UTC_mon,GPS_Data.UTC_day,GPS_Data.UTC_hor,GPS_Data.UTC_min,GPS_Data.UTC_sec))
        self.label_lat.setText("%s°%s" % (GPS_Data.latitude, GPS_Data.lat_hemisphere))
        self.label_lon.setText("%s°%s" % (GPS_Data.longitude, GPS_Data.lon_hemisphere))
        self.label_speed.setText("%s km/h" % GPS_Data.speed)
        self.label_course.setText("%s°" % GPS_Data.course)
        self.label_declination.setText("%s°" % GPS_Data.declination)
        self.label_declination_dir.setText("%s" % GPS_Data.declination_dir)

        print("*" * 60)
        print("状态:%s; 模式:%s" % (GPS_Data.status, GPS_Data.mode))
        print("时间：%s/%s/%s %s:%s:%s" % (
        GPS_Data.UTC_year, GPS_Data.UTC_mon, GPS_Data.UTC_day, GPS_Data.UTC_hor, GPS_Data.UTC_min, GPS_Data.UTC_sec))
        print("纬度:%s°%s; 经度:%s°%s" % (
        GPS_Data.latitude, GPS_Data.lat_hemisphere, GPS_Data.longitude, GPS_Data.lon_hemisphere))
        print("速率:%s; 航向:%s" % (GPS_Data.speed, GPS_Data.course))

        self.Label_Debug("*" * 60)
        self.Label_Debug("状态:%s; 模式:%s" % (GPS_Data.status, GPS_Data.mode))
        self.Label_Debug("时间：%s/%s/%s %s:%s:%s" % (
        GPS_Data.UTC_year, GPS_Data.UTC_mon, GPS_Data.UTC_day, GPS_Data.UTC_hor, GPS_Data.UTC_min, GPS_Data.UTC_sec))
        self.Label_Debug("纬度:%s°%s; 经度:%s°%s" % (
        GPS_Data.latitude, GPS_Data.lat_hemisphere, GPS_Data.longitude, GPS_Data.lon_hemisphere))
        self.Label_Debug("速率:%s; 航向:%s" % (GPS_Data.speed, GPS_Data.course))

    def MPU6050_Calculate(self, MPU6050_Buff):
        if "$MPU6050" not in MPU6050_Buff:
            return
        MPU6050_Buff = MPU6050_Buff.split(',')
        roll_v = MPU6050_Buff[1]  # 滚转角（roll）x
        roll_dot = MPU6050_Buff[2]
        pitch_v = MPU6050_Buff[3]  # 俯仰角（pitch）y
        pitch_dot = MPU6050_Buff[4]
        yaw_v = MPU6050_Buff[5]  # 偏航角（yaw）z
        yaw_dot = MPU6050_Buff[6]
        self.label_roll_v.setText(roll_v)
        self.label_roll_dot.setText(roll_dot)
        self.label_pitch_v.setText(pitch_v)
        self.label_pitch_dot.setText(pitch_dot)
        self.label_yaw_v.setText(yaw_v)
        self.label_yaw_dot.setText(yaw_dot)
        with open(os.getcwd()+r'\mpu6050.txt',"a+") as f:
        	string = "%s,%s;%s,%s;%s,%s;\r\n" % (roll_v,roll_dot,pitch_v,pitch_dot,yaw_v,yaw_dot)
        	f.write(string)
        	f.close()

    def gps2baidu(self, longitude, latitude):
        try:
            url_base = r'http://api.map.baidu.com/geoconv/v1/?from=1'
            ak = ''
            coords = str(longitude) + ',' + str(latitude)
            url = "%s&ak=%s&coords=%s" % (url_base, ak, coords)
            html_json = requests.get(url).json()
            longitude_baidu = html_json['result'][0]['x']  # 经度
            latitude_baidu = html_json['result'][0]['y']  # 纬度
        except Exception as e:
            print(e)
            url = "http://map.yanue.net/gpsapi.php?lat=%s&lng=%s&" % (latitude, longitude)
            html_json = requests.get(url).json()
            longitude_baidu = html_json['baidu']['lng']  # 经度
            latitude_baidu = html_json['baidu']['lat']  # 纬度
        return longitude_baidu, latitude_baidu

    def map_show(self, longitude, latitude):
        url_base = r'http://api.map.baidu.com/staticimage/v2?'
        center = str(longitude) + ',' + str(latitude)
        markers = str(longitude) + ',' + str(latitude)
        ak = ''
        height = 600
        width = 600
        url = "%s&zoom=19&ak=%s&center=%s&markers=%s&height=%s&width=%s" % (
            url_base, ak, center, markers, height, width)
        html = requests.get(url)
        self.Label_Debug(">> 获取静态地图 <<")
        print(">> 获取静态地图 <<")
        with open("map.jpg", 'wb') as f:
            f.write(html.content)
            f.close()

    def gps_map_main(self, longitude, latitude):
        global longitude_last
        global latitude_last
        if GPS_Data.status != 'A' or GPS_Data.mode != 'A':
            self.Label_Debug(">> 无效定位 <<")
            print(">> 无效定位 <<")
            return
        if longitude_last == longitude or latitude_last == latitude:
            self.Label_Debug(">> 坐标未更新 <<")
            print(">> 坐标未更新 <<")
            self.label_gpsupdate.setStyleSheet("color: rgb(0, 255, 0);;")
            self.label_gpsupdate.setText("坐标未更新")
            return
        self.Label_Debug(">> 有效定位 <<")
        print(">> 有效定位 <<")
        longitude_last = longitude
        latitude_last = latitude
        lon_baidu, lat_baidu = self.gps2baidu(longitude, latitude)
        self.Label_Debug(">> 坐标已更新 <<")
        print(">> 坐标已更新 <<")
        self.label_gpsupdate.setStyleSheet("color: rgb(255, 0, 0);")
        self.label_gpsupdate.setText("坐标已更新")

        self.gps_list_string += ("%s,%s;" % (longitude, latitude))
        self.map_show(lon_baidu, lat_baidu)
        self.Update_GPSImage()

        with open(os.getcwd()+r'\gps.txt',"a+") as f:
        	print(os.getcwd()+"gps.txt")
        	string = "UTC:%s/%s/%s %s:%s:%s; 纬度:%s°%s; 经度:%s°%s; 速率:%s; 航向:%s\r\n" % (GPS_Data.UTC_year, GPS_Data.UTC_mon, GPS_Data.UTC_day, GPS_Data.UTC_hor, GPS_Data.UTC_min, GPS_Data.UTC_sec,GPS_Data.latitude, GPS_Data.lat_hemisphere, GPS_Data.longitude, GPS_Data.lon_hemisphere,GPS_Data.speed, GPS_Data.course)
        	f.write(string)
        	f.close()


    def Update_GPSImage(self):
        image = Image.open('map.jpg')
        image.save('map.png')
        print("OK - 0")
        pix = QPixmap('map.png')
        print("OK - 1")
        self.label_img.setPixmap(pix)
        print("OK - 2")
        QApplication.processEvents()
        os.remove('map.jpg')
        os.remove('map.png')
        print("OK - 3")


################################强制关闭线程##################################################
    def _async_raise(self, tid, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def stop_thread(self, thread):
        self._async_raise(thread.ident, SystemExit)
###############################################################################################


def ui_main():
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = MyMainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    ui_main()


