# -*- coding: utf-8 -*-

import os
import csv

# with open(os.getcwd()+r'\gps.txt', 'r') as f:
# 	with open(os.getcwd()+r'\gps.csv', 'w', newline='') as f_csv:
# 		contents = f.readlines()
# 		for i in contents:
# 			lists = i.split(';')
# 			UTC = "%s:%s:%s" % (int(lists[0].split(':')[1].split(' ')[1])-4,lists[0].split(':')[2],lists[0].split(':')[3])
# 			weidu = lists[1].split(':')[1].strip('N')
# 			jingdu = lists[2].split(':')[1].strip('E')
# 			speed = lists[3].split(':')[1]
# 			hangxiang = lists[4].split(':')[1]
# 			# print(UTC,weidu,jingdu,speed,hangxiang)
# 			csv_writer = csv.writer(f_csv)
# 			csv_row = [str(UTC),str(weidu),str(jingdu),str(speed),str(hangxiang)]
# 			csv_writer.writerow(csv_row)
# 		f_csv.close()
# 	f.close()



with open(os.getcwd()+r'\mpu6050.txt', 'r') as f:
	with open(os.getcwd()+r'\mpu6050.csv', 'w', newline='') as f_csv:
		contents = f.readlines()
		for i in contents:
			lists = i.split(';')
			# print(lists[0].split(',')[1])
			roll_v = lists[0].split(',')[0].strip()
			roll_dot = lists[0].split(',')[1].strip()
			pitch_v = lists[1].split(',')[0].strip()
			pitch_dot = lists[1].split(',')[1].strip()
			yaw_v = lists[2].split(',')[0].strip()
			yaw_dot = lists[2].split(',')[1].strip()
			csv_writer = csv.writer(f_csv)
			csv_row = [str(roll_v),str(roll_dot),str(pitch_v),str(pitch_dot),str(yaw_v),str(yaw_dot)]
			csv_writer.writerow(csv_row)
		f_csv.close()
	f.close()






















