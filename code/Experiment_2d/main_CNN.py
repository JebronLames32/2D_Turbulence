# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 10:10:03 2023

@author: andres cremades botella

File containing the configuration of the CNN model and the training process
"""
import os
os.environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'
import ann_config as ann
import numpy as np
import get_data_fun as gd


CNN = ann.convolutional_residual(ngpu=8)
dy = 1
dx = 1
# change the dimensions of the input data
shpy = int((500-1)/dy)+1
shpx = int((500-1)/dx)+1
CNN.define_model(shp=(shpx,shpy,2),learat=8e-4,nfil=[16,32,64]) 
CNN.train_model(1000,1099,delta_t=10,delta_e=10,max_epoch=50,\
                batch_size=4,down_y=dy,down_x=dx) 

print('fin')