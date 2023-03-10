#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  load_data.py
#  
#  Author Ene SS Rawa / Tjitse van der Molen  
 

# # # # # import libraries # # # # #

import os
import csv
import shutil
import numpy as np
from datetime import datetime


def load_csv_data(CHANNELS, DATA_DIR_PATH, TEMP_THREAD_DIR_PATH):
	"""
	Merges data from different channels and combines thread data in dir
	
	Input:
	CHANNELS - [str] : list of channel names to be used in analysis.
		channel names should correspond to the directory names with the 
		data in DATA_DIR_PATH.
	DATA_DIR_PATH - str : path to directory where data is stored
	TEMP_THREAD_DIR_PATH - str : path to directory where thread data 
		from different channels should be combined
		
	Output:
	data - np array : loaded contents of (combined) csv files
	all thread .csv files are stored in TEMP_THREAD_DIR_PATH
	"""
	
	print("Loading data from:")
	
	# for each channel
	for i, channel in enumerate(CHANNELS):
		
		print(channel)
				
		# obtain file and subdirectory names in directory
		dir_names = os.listdir(DATA_DIR_PATH + channel)
		
		# obtain file name of csv file
		file_name = [j for j in dir_names if ".csv" in j]
			
		# check if correct number of file names are loaded	
		if len(file_name) == 0:
			print("ERROR no .csv file in {}".format(DATA_DIR_PATH + channel))
			return 0
		elif len(file_name) > 1:
			print("ERROR more than one .csv file in {}. Only using first entry: {}".format(DATA_DIR_PATH + channel, file_name[0]))
		
		
		# set error count to 0
		error_count = 0		
							
		# if this is the first channel that is loaded
		if i == 0:
					
			# load channel data into numpy array
			with open(DATA_DIR_PATH + channel + "/" + file_name[0], 'r') as x:
				
				# # store results
				# data = np.array(list(csv.reader(x, delimiter=",")),dtype=object)
				
				chan_data_obj = csv.reader(x, delimiter=",")
				
				# add content to array in less efficient way (TEMPORARY SOLUTION)
				for j, line in enumerate(chan_data_obj):
																												
					# if the line is not the right size, split it at comma separation
					if len(line) != 10:
						line = line[0].split(",")
					
					if len(line) == 10:	
					
						# if this is the header	
						if j == 0:
						
							# intiate data array with line
							data = np.array(line)
													
						else:
								
							# add line to data array
							data = np.vstack((data, np.array(line)))
							
					else:
						
						error_count += 1
			
		else:
			
			# try to load the data and add to the existing numpy array
			try:
				
				# load channel data into numpy array
				with open(DATA_DIR_PATH + channel + "/" + file_name[0], 'r') as x:
					chan_data = np.array(list(csv.reader(x, delimiter=",")),dtype=object)
							
				# append chan_data without header to data numpy array
				data = np.vstack((data, chan_data[1:,:]))
							
			# if data in csv file is depricated
			except:
				
				# load channel data into numpy array
				with open(DATA_DIR_PATH + channel + "/" + file_name[0], 'r') as x:
					
					chan_data_obj = csv.reader(x, delimiter=",")
				
					# add content to array in less efficient way (TEMPORARY SOLUTION)
					for j, line in enumerate(chan_data_obj):
						
						# if the line is not the right size (likely "," in messages cause errors)
						if len(line) != data.shape[1]:
							line = line[0].split(",")
						
						# if the line is the right size (likely "," in messages cause errors)
						if len(line) == data.shape[1]:	
						
							# if this is not the header	
							if j != 0:
							
								# add line to data array
								data = np.vstack((data, np.array(line)))
								
						else:
							
							error_count += 1
						
		
		
		# print error count
		print("{} messages could not be loaded".format(error_count))
		
		
		# if there is thread data for this channel
		if os.path.exists(DATA_DIR_PATH + channel + "/threads"):
			
			# obtain all file names in thread folder
			thread_names = os.listdir(DATA_DIR_PATH + channel + "/threads")
								
			# for each thread file
			for thr_file in thread_names:
			
				# copy thread file to temporary directory
				shutil.copy(DATA_DIR_PATH + channel + "/threads/" + thr_file, TEMP_THREAD_DIR_PATH)
		
	print("")
		
	return data


