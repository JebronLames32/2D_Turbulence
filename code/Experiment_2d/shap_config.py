# -*- coding: utf-8 -*-
"""
Created on Tue Jun 27 12:58:26 2023

@author: andres cremades botella

File containing the functions of the SHAP
"""
import numpy as np
import os

class shap_conf():
    
    def __init__(self,filecnn='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/trained_model.h5'):
        """
        Initialization of the SHAP class
        """
        import ann_config as ann
        self.background = None
        CNN = ann.convolutional_residual()
        CNN.load_ANN()
        self.model = CNN.model
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/SHAP_fields_io/')
        except:
            pass
        
    def calc_shap_kernel(self,start=1,end=2,step=1,\
                         file='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/SHAP_fields_io/vel_',\
                         fileuvw='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newdata/hdf5/vel_',\
                         fileQ='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Q_fields_io/vel_',\
                         filenorm="/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/norm.txt",padpix=15,dy=1,dx=1,\
                         testcases=False,filetest='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/ind_val.txt',volfilt=1e8,\
                         numfield=-1,fieldini=0,norep=False):
        import get_data_fun as gd
        import shap 
        import glob
        normdata = gd.get_data_norm(file_read=fileuvw)
        normdata.geom_param(start,delta_y=dy,delta_x=dx)
        try:
            normdata.read_norm(file=filenorm)
        except:
            normdata.calc_norm(start,end)
        self.create_background(normdata)
        self.shap_values = []
        if testcases:
            file_read = open(filetest,"r")
            listcases = np.array(file_read.readline().replace('[','').\
                                 replace(']','').split(','),dtype='int')[::step]
            if numfield > 0:
                if numfield+fieldini < len(listcases):
                    listcases = listcases[fieldini:fieldini+numfield]
                else:
                    listcases = listcases[fieldini:]
        else:
            listcases = range(start,end,step)
        for ii in listcases:
            fileQ_ii = fileQ+str(ii)+'*.h5'
            fileQ_ii2 = glob.glob(fileQ_ii)[0]        
            index_piv = fileQ_ii2.find('vel_')
            fileshap_ii = file+fileQ_ii2[index_piv+3:]
            fileshap_ii = fileQ_ii2.replace('Q','SHAP')
            if norep and len(glob.glob(fileshap_ii)) > 0:
                continue
            uv_struc = normdata.read_uvstruc(fileQ_ii=fileQ_ii2)
            uvmax = np.max(uv_struc.mat_segment_filtered)
            self.segmentation = uv_struc.mat_segment_filtered-1
            self.segmentation[self.segmentation==-1] = uvmax
            uu_i,vv_i = normdata.read_velocity(ii,padpix=padpix)
            self.input = normdata.norm_velocity(uu_i,vv_i)[0,:,:,:]
            uu_o,vv_o = normdata.read_velocity(ii,out=True,padpix=padpix)
            self.output = normdata.norm_velocity(uu_o,vv_o)[0,:,:,:]
            self.index_vol = np.where(uv_struc.vol > volfilt)[0]
            self.event_filter = uv_struc.event[self.index_vol]
            nmax2 = len(self.event_filter)+1
            zshap = np.ones((1,nmax2))
            explainer = shap.KernelExplainer(self.model_function,\
                                             np.zeros((1,nmax2)))
#            shap_values = explainer.shap_values(zshap,nsamples="auto")[0][0] 
            shap_values = explainer.shap_values(zshap,nsamples=500)[0][0]   
            self.write_output(shap_values,fileshap_ii)
            
    def write_output(self,shap,fileshap_ii):
        """
        Write the structures shap and geometric characteristics
        """ 
        import h5py
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/SHAP_fields_io/')
        except:
            pass
        hf = h5py.File(fileshap_ii, 'w')
        hf.create_dataset('SHAP', data=shap)
        
    def read_shap(self,fileSHAP_ii):
        """
        Function for read the SHAP values
        """
        import h5py
        hf = h5py.File(fileSHAP_ii, 'r+')
        shap_values = np.array(hf['SHAP'])
        return shap_values
    
    def eval_shap(self,start=1,end=2,step=1,\
                  fileshap='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/SHAP_fields_io/vel_',\
                  fileuvw='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newdata/hdf5/vel_',\
                  fileQ='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Q_fields_io/vel_',\
                  filenorm="/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/norm.txt",padpix=15,dy=1,dx=1,\
                  testcases=False,filetest='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/ind_val.txt',volfilt=1e8):
        """
        Function to evaluate the value of the mse calculated by SHAP and by the 
        model
        """
        import get_data_fun as gd
        import glob
        normdata = gd.get_data_norm(file_read=fileuvw)
        normdata.geom_param(start,delta_y=dy,delta_x=dx)
        try:
            normdata.read_norm(file=filenorm)
        except:
            normdata.calc_norm(start,end)
        self.create_background(normdata)
        self.error_mse2 = []
        if testcases:
            file_read = open(filetest,"r")
            listcases = np.array(file_read.readline().replace('[','').\
                                 replace(']','').split(','),dtype='int')[::step]
        else:
            listcases = range(start,end,step)
        for ii in listcases:
            fileQ_ii = fileQ+'.'+str(ii)+'.*.h5.Q'
            fileQ_ii2 = glob.glob(fileQ_ii)[0]
            fileSHAP_ii = fileshap+'.'+str(ii)+'.*.h5.SHAP'
            fileSHAP_ii2 = glob.glob(fileSHAP_ii)[0]
            uv_struc = normdata.read_uvstruc(fileQ_ii=fileQ_ii2)
            uvmax = np.max(uv_struc.mat_segment_filtered)
            self.segmentation = uv_struc.mat_segment_filtered-1
            self.segmentation[self.segmentation==-1] = uvmax
            uu_i,vv_i = normdata.read_velocity(ii,padpix=padpix)
            self.input = normdata.norm_velocity(uu_i,vv_i)[0,:,:,:]
            input_field = self.input.copy()
            uu_o,vv_o = normdata.read_velocity(ii,out=True,padpix=padpix)
            self.output = normdata.norm_velocity(uu_o,vv_o)[0,:,:,:]
            self.index_vol = np.where(uv_struc.vol > volfilt)[0]
            self.event_filter = uv_struc.event[self.index_vol]
            nmax2 = len(self.event_filter)+1
            zs = np.zeros((1,nmax2))
            mse_f = self.shap_model_kernel(input_field)
            shap_val = self.read_shap(fileSHAP_ii2)
            shap0 = self.model_function(zs)[0][0]
            mse_g = np.sum(shap_val)+shap0
            error_mse2 = (mse_f-mse_g)**2
            print(error_mse2)
            self.error_mse2.append(error_mse2)        
        import h5py
        hf = h5py.File('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/mse_fg2.h5', 'w')
        hf.create_dataset('mse_fg2', data=self.error_mse2)
        
        
    def mask_dom(self,zs):
        """
        Function for making the domain
        """
        # If no background is defined the mean value of the field is taken
        if self.background is None:
            self.background = self.input.mean((0,1))*np.ones((3,))
        mask_out = self.input.copy()
        # Replace the values of the field in which the feature is deleted
        for jj in range(zs.shape[0]):
            if zs[jj] == 0:
                mask_out[self.segmentation == jj,:] = self.background
        return mask_out
    
    def shap_model_kernel(self,model_input):
        """
        Model to calculate the shap value
        """
        input_pred = model_input.reshape(1,model_input.shape[0],\
                                         model_input.shape[1],\
                                             model_input.shape[2])
        pred = self.model.predict(input_pred)
        len_x = self.output.shape[0]
        len_y = self.output.shape[1]
        mse  = np.mean(np.sqrt((self.output.reshape(-1,len_x,len_y,2)\
                                -pred)**2))
        return mse
    
    def model_function(self,zs):
        ii = 0
        lm = zs.shape[0]
        mse = np.zeros((lm,1))
        for zii in zs:
            print('Calculating SHAP: '+str(ii/lm))
            model_input = self.mask_dom(zii)
            mse[ii,0] = self.shap_model_kernel(model_input)
            ii += 1
        return mse

    def create_background(self,data,value=0):
        """
        Function for generating the bacground value
        """
        self.background = np.zeros((2,))
        self.background[0] = (value-data.uumin)/(data.uumax-data.uumin)
        self.background[1] = (value-data.vvmin)/(data.vvmax-data.vvmin)
        
    def read_data(self,start=1,end=2,step=1,\
                   file='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/SHAP_fields_io/vel_',\
                   fileQ='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Q_fields_io/vel_',\
                   fileuvw='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newdata/hdf5/vel_',\
                   filenorm="/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/norm.txt",\
                   colormap='viridis',absolute=False,testcases=False,\
                   filetest='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/ind_val.txt',numfield=-1,fieldini=0,dx=1,dy=1,\
                   volfilt=1e8,wallattach=False,padpix=15,saveuv=False,\
                   filereystr='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Reynoldsstress_fields_io/vel_',shapmin=-30,\
                   shapmax=30,shapminvol=-30,shapmaxvol=30,nbars=1000,editq3=False,\
                   readdata=False,fileread='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/data_plots.h5.Q'):
        """
        Read data
        """ 
        self.nbars = nbars
        import get_data_fun as gd
        import glob
        import h5py
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Reynoldsstress_fields_io/')
        except:
            pass
        self.wallattach = wallattach
        normdata = gd.get_data_norm(file_read=fileuvw)
        normdata.geom_param(start,delta_x=dx,delta_y=dy)
        if absolute:
            self.ylabel_shap = '$|\phi_i| \cdot 10^{-3}$'
            self.ylabel_shap_vol = '$|\phi_i/S^+| \cdot 10^{-9}$'
        else:
            self.ylabel_shap = '$\phi_i \cdot 10^{-3}$'
            self.ylabel_shap_vol = '$\phi_i/S^+ \cdot 10^{-9}$'
        if readdata:
            hf = h5py.File(fileread, 'r')
            self.volume_wa = np.array(hf['volume_wa'])
            self.volume_wd = np.array(hf['volume_wd'])
            self.shap_wa = np.array(hf['shap_wa'])
            self.shap_wd = np.array(hf['shap_wd'])
            self.shap_wa_vol = np.array(hf['shap_wa_vol'])
            self.shap_wd_vol = np.array(hf['shap_wd_vol'])
            self.event_wa = np.array(hf['event_wa'])
            self.event_wd = np.array(hf['event_wd'])
            self.uv_uvtot_wa = np.array(hf['uv_uvtot_wa'])
            self.uv_uvtot_wd = np.array(hf['uv_uvtot_wd'])
            self.uv_uvtot_wa_vol = np.array(hf['uv_uvtot_wa_vol'])
            self.uv_uvtot_wd_vol = np.array(hf['uv_uvtot_wd_vol'])
            self.uv_vol_uvtot_vol_wa = np.array(hf['uv_vol_uvtot_vol_wa'])
            self.uv_vol_uvtot_vol_wd = np.array(hf['uv_vol_uvtot_vol_wd'])
            self.volume_1 = np.array(hf['volume_1'])
            self.volume_2 = np.array(hf['volume_2'])
            self.volume_3 = np.array(hf['volume_3'])
            self.volume_4 = np.array(hf['volume_4'])
            self.volume_1_wa = np.array(hf['volume_1_wa'])
            self.volume_2_wa = np.array(hf['volume_2_wa'])
            self.volume_3_wa = np.array(hf['volume_3_wa'])
            self.volume_4_wa = np.array(hf['volume_4_wa'])
            self.volume_1_wd = np.array(hf['volume_1_wd'])
            self.volume_2_wd = np.array(hf['volume_2_wd'])
            self.volume_3_wd = np.array(hf['volume_3_wd'])
            self.volume_4_wd = np.array(hf['volume_4_wd'])
            self.shap_1 = np.array(hf['shap_1'])
            self.shap_2 = np.array(hf['shap_2'])
            self.shap_3 = np.array(hf['shap_3'])
            self.shap_4 = np.array(hf['shap_4'])
            self.shap_1_wa = np.array(hf['shap_1_wa'])
            self.shap_2_wa = np.array(hf['shap_2_wa'])
            self.shap_3_wa = np.array(hf['shap_3_wa'])
            self.shap_4_wa = np.array(hf['shap_4_wa'])
            self.shap_1_wd = np.array(hf['shap_1_wd'])
            self.shap_2_wd = np.array(hf['shap_2_wd'])
            self.shap_3_wd = np.array(hf['shap_3_wd'])
            self.shap_4_wd = np.array(hf['shap_4_wd'])
            self.shap_1_vol = np.array(hf['shap_1_vol'])
            self.shap_2_vol = np.array(hf['shap_2_vol'])
            self.shap_3_vol = np.array(hf['shap_3_vol'])
            self.shap_4_vol = np.array(hf['shap_4_vol'])
            self.shap_1_vol_wa = np.array(hf['shap_1_vol_wa'])
            self.shap_2_vol_wa = np.array(hf['shap_2_vol_wa'])
            self.shap_3_vol_wa = np.array(hf['shap_3_vol_wa'])
            self.shap_4_vol_wa = np.array(hf['shap_4_vol_wa'])
            self.shap_1_vol_wd = np.array(hf['shap_1_vol_wd'])
            self.shap_2_vol_wd = np.array(hf['shap_2_vol_wd'])
            self.shap_3_vol_wd = np.array(hf['shap_3_vol_wd'])
            self.shap_4_vol_wd = np.array(hf['shap_4_vol_wd'])
            self.uv_uvtot_1 = np.array(hf['uv_uvtot_1'])
            self.uv_uvtot_2 = np.array(hf['uv_uvtot_2'])
            self.uv_uvtot_3 = np.array(hf['uv_uvtot_3'])
            self.uv_uvtot_4 = np.array(hf['uv_uvtot_4'])
            self.uv_uvtot_1_wa = np.array(hf['uv_uvtot_1_wa'])
            self.uv_uvtot_2_wa = np.array(hf['uv_uvtot_2_wa'])
            self.uv_uvtot_3_wa = np.array(hf['uv_uvtot_3_wa'])
            self.uv_uvtot_4_wa = np.array(hf['uv_uvtot_4_wa'])
            self.uv_uvtot_1_wd = np.array(hf['uv_uvtot_1_wd'])
            self.uv_uvtot_2_wd = np.array(hf['uv_uvtot_2_wd'])
            self.uv_uvtot_3_wd = np.array(hf['uv_uvtot_3_wd'])
            self.uv_uvtot_4_wd = np.array(hf['uv_uvtot_4_wd'])
            self.uv_uvtot_1_vol = np.array(hf['uv_uvtot_1_vol'])
            self.uv_uvtot_2_vol = np.array(hf['uv_uvtot_2_vol'])
            self.uv_uvtot_3_vol = np.array(hf['uv_uvtot_3_vol'])
            self.uv_uvtot_4_vol = np.array(hf['uv_uvtot_4_vol'])
            self.uv_uvtot_1_vol_wa = np.array(hf['uv_uvtot_1_vol_wa'])
            self.uv_uvtot_2_vol_wa = np.array(hf['uv_uvtot_2_vol_wa'])
            self.uv_uvtot_3_vol_wa = np.array(hf['uv_uvtot_3_vol_wa'])
            self.uv_uvtot_4_vol_wa = np.array(hf['uv_uvtot_4_vol_wa'])
            self.uv_uvtot_1_vol_wd = np.array(hf['uv_uvtot_1_vol_wd'])
            self.uv_uvtot_2_vol_wd = np.array(hf['uv_uvtot_2_vol_wd'])
            self.uv_uvtot_3_vol_wd = np.array(hf['uv_uvtot_3_vol_wd'])
            self.uv_uvtot_4_vol_wd = np.array(hf['uv_uvtot_4_vol_wd'])
            self.uv_vol_uvtot_vol_1 = np.array(hf['uv_vol_uvtot_vol_1'])
            self.uv_vol_uvtot_vol_2 = np.array(hf['uv_vol_uvtot_vol_2'])
            self.uv_vol_uvtot_vol_3 = np.array(hf['uv_vol_uvtot_vol_3'])
            self.uv_vol_uvtot_vol_4 = np.array(hf['uv_vol_uvtot_vol_4'])
            self.uv_vol_uvtot_vol_1_wa = np.array(hf['uv_vol_uvtot_vol_1_wa'])
            self.uv_vol_uvtot_vol_2_wa = np.array(hf['uv_vol_uvtot_vol_2_wa'])
            self.uv_vol_uvtot_vol_3_wa = np.array(hf['uv_vol_uvtot_vol_3_wa'])
            self.uv_vol_uvtot_vol_4_wa = np.array(hf['uv_vol_uvtot_vol_4_wa'])
            self.uv_vol_uvtot_vol_1_wd = np.array(hf['uv_vol_uvtot_vol_1_wd'])
            self.uv_vol_uvtot_vol_2_wd = np.array(hf['uv_vol_uvtot_vol_2_wd'])
            self.uv_vol_uvtot_vol_3_wd = np.array(hf['uv_vol_uvtot_vol_3_wd'])
            self.uv_vol_uvtot_vol_4_wd = np.array(hf['uv_vol_uvtot_vol_4_wd'])
            self.event_1 = np.array(hf['event_1'])
            self.event_2 = np.array(hf['event_2'])
            self.event_3 = np.array(hf['event_3'])
            self.event_4 = np.array(hf['event_4'])
            self.event_1_wa = np.array(hf['event_1_wa'])
            self.event_2_wa = np.array(hf['event_2_wa'])
            self.event_3_wa = np.array(hf['event_3_wa'])
            self.event_4_wa = np.array(hf['event_4_wa'])
            self.event_1_wd = np.array(hf['event_1_wd'])
            self.event_2_wd = np.array(hf['event_2_wd'])
            self.event_3_wd = np.array(hf['event_3_wd'])
            self.event_4_wd = np.array(hf['event_4_wd'])
            self.voltot = np.array(hf['voltot'])
            self.shapback_list = np.array(hf['shapback_list'])
            self.shapbackvol_list = np.array(hf['shapbackvol_list'])
            self.AR1_grid = np.array(hf['AR1_grid'])
            self.SHAP_grid1 = np.array(hf['SHAP_grid1'])
            self.SHAP_grid2 = np.array(hf['SHAP_grid2'])
            self.SHAP_grid3 = np.array(hf['SHAP_grid3'])
            self.SHAP_grid4 = np.array(hf['SHAP_grid4'])
            self.SHAP_grid1vol = np.array(hf['SHAP_grid1vol'])
            self.SHAP_grid2vol = np.array(hf['SHAP_grid2vol'])
            self.SHAP_grid3vol = np.array(hf['SHAP_grid3vol'])
            self.SHAP_grid4vol = np.array(hf['SHAP_grid4vol'])
            self.npoin1 = np.array(hf['npoin1'])
            self.npoin2 = np.array(hf['npoin2'])
            self.npoin3 = np.array(hf['npoin3'])
            self.npoin4 = np.array(hf['npoin4'])
            self.shap1cum = np.array(hf['shap1cum'])
            self.shap2cum = np.array(hf['shap2cum'])
            self.shap3cum = np.array(hf['shap3cum'])
            self.shap4cum = np.array(hf['shap4cum'])
            self.shapbcum = np.array(hf['shapbcum'])
            self.shap_vol1cum = np.array(hf['shap_vol1cum'])
            self.shap_vol2cum = np.array(hf['shap_vol2cum'])
            self.shap_vol3cum = np.array(hf['shap_vol3cum'])
            self.shap_vol4cum = np.array(hf['shap_vol4cum'])
            self.shap_volbcum = np.array(hf['shap_volbcum'])
            self.shapmax = np.array(hf['shapmax'])
            self.shapmin = np.array(hf['shapmin'])
            self.shapmaxvol = np.array(hf['shapmaxvol'])
            self.shapminvol = np.array(hf['shapminvol'])
            self.cdg_y_1 = np.array(hf['cdg_y_1'])
            self.cdg_y_2 = np.array(hf['cdg_y_2'])
            self.cdg_y_3 = np.array(hf['cdg_y_3'])
            self.cdg_y_4 = np.array(hf['cdg_y_4'])
            self.cdg_y_wa = np.array(hf['cdg_y_wa'])
            self.cdg_y_wd = np.array(hf['cdg_y_wd'])
            self.dxdy_1 = np.array(hf['dxdy_1'])
            self.dxdy_2 = np.array(hf['dxdy_2'])
            self.dxdy_3 = np.array(hf['dxdy_3'])
            self.dxdy_4 = np.array(hf['dxdy_4'])
            self.dxdy_wa = np.array(hf['dxdy_wa'])
            self.dxdy_wd = np.array(hf['dxdy_wd'])
            hf.close()
        else:
            self.volume_wa = []
            self.volume_wd = []
            self.shap_wa = []
            self.shap_wd = []
            self.shap_wa_vol = []
            self.shap_wd_vol = []
            self.event_wa = []
            self.event_wd = []
            self.uv_uvtot_wa = []
            self.uv_uvtot_wd = []
            self.uv_uvtot_wa_vol = []
            self.uv_uvtot_wd_vol = []
            self.uv_vol_uvtot_vol_wa = []
            self.uv_vol_uvtot_vol_wd = []
            self.cdg_y_wa = []
            self.cdg_y_wd = []
            self.dxdy_wa = []
            self.dxdy_wd = []
            self.volume_1 = []
            self.uv_uvtot_1 = []
            self.uv_uvtot_1_vol = []
            self.uv_vol_uvtot_vol_1 = []
            self.shap_1 = []
            self.shap_1_vol = []
            self.event_1 = []
            self.cdg_y_1 = []
            self.dxdy_1 = []
            self.volume_1_wa = []
            self.uv_uvtot_1_wa = []
            self.uv_uvtot_1_vol_wa = []
            self.uv_vol_uvtot_vol_1_wa = []
            self.shap_1_wa = []
            self.shap_1_vol_wa = []
            self.event_1_wa = []
            self.volume_1_wd = []
            self.uv_uvtot_1_wd = []
            self.uv_uvtot_1_vol_wd = []
            self.uv_vol_uvtot_vol_1_wd = []
            self.shap_1_wd = []
            self.shap_1_vol_wd = []
            self.event_1_wd = []
            self.volume_2 = []
            self.uv_uvtot_2 = []
            self.uv_uvtot_2_vol = []
            self.uv_vol_uvtot_vol_2 = []
            self.shap_2 = []
            self.shap_2_vol = []
            self.event_2 = []
            self.cdg_y_2 = []
            self.dxdy_2 = []
            self.volume_2_wa = []
            self.uv_uvtot_2_wa = []
            self.uv_uvtot_2_vol_wa = []
            self.uv_vol_uvtot_vol_2_wa = []
            self.shap_2_wa = []
            self.shap_2_vol_wa = []
            self.event_2_wa = []
            self.volume_2_wd = []
            self.uv_uvtot_2_wd = []
            self.uv_uvtot_2_vol_wd = []
            self.uv_vol_uvtot_vol_2_wd = []
            self.shap_2_wd = []
            self.shap_2_vol_wd = []
            self.event_2_wd = []
            self.volume_3 = []
            self.uv_uvtot_3 = []
            self.uv_uvtot_3_vol = []
            self.uv_vol_uvtot_vol_3 = []
            self.shap_3 = []
            self.shap_3_vol = []
            self.event_3 = []
            self.cdg_y_3 = []
            self.dxdy_3 = []
            self.volume_3_wa = []
            self.uv_uvtot_3_wa = []
            self.uv_uvtot_3_vol_wa = []
            self.uv_vol_uvtot_vol_3_wa = []
            self.shap_3_wa = []
            self.shap_3_vol_wa = []
            self.event_3_wa = []
            self.volume_3_wd = []
            self.uv_uvtot_3_wd = []
            self.uv_uvtot_3_vol_wd = []
            self.uv_vol_uvtot_vol_3_wd = []
            self.shap_3_wd = []
            self.shap_3_vol_wd = []
            self.event_3_wd = []
            self.volume_4 = []
            self.uv_uvtot_4 = []
            self.uv_uvtot_4_vol = []
            self.uv_vol_uvtot_vol_4 = []
            self.shap_4 = []
            self.shap_4_vol = []
            self.event_4 = []
            self.cdg_y_4 = []
            self.dxdy_4 = []
            self.volume_4_wa = []
            self.uv_uvtot_4_wa = []
            self.uv_uvtot_4_vol_wa = []
            self.uv_vol_uvtot_vol_4_wa = []
            self.shap_4_wa = []
            self.shap_4_vol_wa = []
            self.event_4_wa = []
            self.volume_4_wd = []
            self.uv_uvtot_4_wd = []
            self.uv_uvtot_4_vol_wd = []
            self.uv_vol_uvtot_vol_4_wd = []
            self.shap_4_wd = []
            self.shap_4_vol_wd = []
            self.event_4_wd = []
            self.shapback_list = []
            self.shapbackvol_list = []
            self.voltot = np.sum(normdata.vol)
            expmax = 2
            expmin = -1
            ngrid = 50
            AR1_vec = np.linspace(expmin,expmax,ngrid+1)
            self.AR1_grid = np.zeros((ngrid,))
            self.SHAP_grid1 = np.zeros((ngrid,))
            self.SHAP_grid2 = np.zeros((ngrid,))
            self.SHAP_grid3 = np.zeros((ngrid,))
            self.SHAP_grid4 = np.zeros((ngrid,))
            self.SHAP_grid1vol = np.zeros((ngrid,))
            self.SHAP_grid2vol = np.zeros((ngrid,))
            self.SHAP_grid3vol = np.zeros((ngrid,))
            self.SHAP_grid4vol = np.zeros((ngrid,))
            self.npoin1 = np.zeros((ngrid,))
            self.npoin2 = np.zeros((ngrid,))
            self.npoin3 = np.zeros((ngrid,))
            self.npoin4 = np.zeros((ngrid,))
            for ii_arlim1 in np.arange(ngrid):
                arlim1inf = 10**AR1_vec[ii_arlim1]
                arlim1sup = 10**AR1_vec[ii_arlim1+1]
                self.AR1_grid[ii_arlim1] = 10**((AR1_vec[ii_arlim1]+AR1_vec[ii_arlim1+1])/2)
            self.shap1cum = 0
            self.shap2cum = 0
            self.shap3cum = 0
            self.shap4cum = 0
            self.shap_vol1cum = 0
            self.shap_vol2cum = 0
            self.shap_vol3cum = 0
            self.shap_vol4cum = 0
            self.shapbcum = 0
            self.shap_volbcum = 0
            if testcases:
                file_read = open(filetest,"r")
                listcases = np.array(file_read.readline().replace('[','').\
                                     replace(']','').split(','),dtype='int')[::step]
                if numfield > 0:
                    if numfield+fieldini < len(listcases):
                        listcases = listcases[fieldini:fieldini+numfield]
                    else:
                        listcases = listcases[fieldini:]
                elif fieldini > 0:
                    listcases = listcases[fieldini:]
            else:
                listcases = range(start,end,step)
            numfield = 0
            for ii in listcases:
                fileQ_ii = fileQ+str(ii)+'*.h5'
                fileQ_ii2 = glob.glob(fileQ_ii)[0]
                fileSHAP_ii = file+str(ii)+'*.h5'
                filereystress_ii = filereystr+'.'+str(ii)+'.'+str(ii+1)+'.h5.reystr'
                try:
                    fileSHAP_ii2 = glob.glob(fileSHAP_ii)[0]
                    uv_struc = normdata.read_uvstruc(fileQ_ii=fileQ_ii2)
                    if editq3:
                        for jjind in np.arange(len(uv_struc.event)):
                            if uv_struc.cdg_y[jjind]>0.9 and uv_struc.event[jjind]==3:
                                uv_struc.event[jjind] = 2
                    uu,vv = normdata.read_velocity(ii,padpix=padpix)
                    uvtot = np.sum(abs(np.multiply(uu,vv)))
                    voltot = np.sum(normdata.vol)
                    self.index_vol = np.where(uv_struc.vol > volfilt)[0]
                    self.event_filter = uv_struc.event[self.index_vol]
                    lenstruc = len(self.event_filter)
                    if absolute:
                        shapvalues = abs(self.read_shap(fileSHAP_ii2))
                        shapback = abs(shapvalues[-1])
                        self.shapmax = np.max(abs(np.array([shapmin,shapmax])))
                        self.shapmin = 0
                        self.shapmaxvol = np.max(abs(np.array([shapminvol,shapmaxvol])))
                        self.shapminvol = 0
                        shapvalues = abs(self.read_shap(fileSHAP_ii2))
                    else:
                        shapvalues = self.read_shap(fileSHAP_ii2)
                        shapback = shapvalues[-1]
                        self.shapmax = np.max(np.array([shapmin,shapmax]))
                        self.shapmin = np.min(np.array([shapmin,shapmax]))
                        self.shapmaxvol = np.max(np.array([shapminvol,shapmaxvol]))
                        self.shapminvol = np.min(np.array([shapminvol,shapmaxvol]))
                        shapvalues = abs(self.read_shap(fileSHAP_ii2))
                    uv = np.zeros((lenstruc,))
                    uv_vol = np.zeros((lenstruc,))
                    uv_Qminus = 0
                    vol_Qminus = 0
                    for jj in np.arange(lenstruc):
                        indexjj = self.index_vol[jj]
                        indexuv = np.where(uv_struc.mat_segment==indexjj+1)
                        for kk in np.arange(len(indexuv[0])):
                            uv[jj] += abs(uu[indexuv[0][kk],indexuv[1][kk]]*\
                              vv[indexuv[0][kk],indexuv[1][kk]]) 
                        uv_vol[jj] = uv[jj]/uv_struc.vol[indexjj]
                    uv_back_vol = (uvtot-np.sum(uv))/\
                    (voltot-np.sum(uv_struc.vol))
                    uv_vol_sum = np.sum(uv_vol)+uv_back_vol
                    for jj in np.arange(lenstruc):
                        indexjj = self.index_vol[jj]
                        if uv_struc.event[indexjj] == 2 or uv_struc.event[indexjj] == 4:
                            uv_Qminus += uv[jj]
                            vol_Qminus += uv_struc.vol[indexjj]
                        uv[jj] /= uvtot
                        yplus_min_ii = (uv_struc.ymin[indexjj])*normdata.rey
                        if uv_struc.vol[indexjj] > volfilt:              
                            Dy = uv_struc.ymax[indexjj]-uv_struc.ymin[indexjj]
                            Dx = uv_struc.dx[indexjj]
                            AR1 = Dx/Dy
                            if wallattach and yplus_min_ii < 20:
                                self.volume_wa.append(uv_struc.vol[indexjj]/1e6)
                                self.shap_wa.append(shapvalues[jj]*1e3)
                                self.shap_wa_vol.append(shapvalues[jj]/uv_struc.vol[indexjj]*1e9)
                                self.event_wa.append(uv_struc.event[indexjj])
                                self.uv_uvtot_wa.append(uv[jj])
                                self.uv_uvtot_wa_vol.append(uv[jj]/uv_struc.vol[indexjj]*1e7)
                                self.uv_vol_uvtot_vol_wa.append(uv_vol[jj]/uv_vol_sum)
                                self.dxdy_wa.append(uv_struc.dx[indexjj]/(uv_struc.ymax[indexjj]-uv_struc.ymin[indexjj]))
                                self.cdg_y_wa.append(uv_struc.cdg_y[indexjj])
                            else:
                                self.volume_wd.append(uv_struc.vol[indexjj]/1e6)
                                self.shap_wd.append(shapvalues[jj]*1e3)
                                self.shap_wd_vol.append(shapvalues[jj]/uv_struc.vol[indexjj]*1e9)
                                self.event_wd.append(uv_struc.event[indexjj])
                                self.uv_uvtot_wd.append(uv[jj])
                                self.uv_uvtot_wd_vol.append(uv[jj]/uv_struc.vol[indexjj]*1e7)
                                self.uv_vol_uvtot_vol_wd.append(uv_vol[jj]/uv_vol_sum)
                                self.dxdy_wd.append(uv_struc.dx[indexjj]/(uv_struc.ymax[indexjj]-uv_struc.ymin[indexjj]))
                                self.cdg_y_wd.append(uv_struc.cdg_y[indexjj])
                            if uv_struc.event[indexjj] == 1:
                                self.volume_1.append(uv_struc.vol[indexjj]/1e6)
                                self.shap_1.append(shapvalues[jj]*1e3)
                                self.shap_1_vol.append(shapvalues[jj]/uv_struc.vol[indexjj]*1e9)
                                self.event_1.append(uv_struc.event[indexjj])
                                self.uv_uvtot_1.append(uv[jj])
                                self.uv_uvtot_1_vol.append(uv[jj]/uv_struc.vol[indexjj]*1e7)
                                self.uv_vol_uvtot_vol_1.append(uv_vol[jj]/uv_vol_sum)
                                self.dxdy_1.append((uv_struc.dx[indexjj]+1e-10)/(uv_struc.ymax[indexjj]-uv_struc.ymin[indexjj]+1e-5))
                                self.shap1cum += shapvalues[jj]
                                self.shap_vol1cum += shapvalues[jj]/uv_struc.vol[indexjj]
                                self.cdg_y_1.append(uv_struc.cdg_y[indexjj])
                                if yplus_min_ii < 20:
                                    self.volume_1_wa.append(uv_struc.vol[jj]/1e6)
                                    self.uv_uvtot_1_wa.append(uv[jj])
                                    self.uv_uvtot_1_vol_wa.append(uv[jj]/uv_struc.vol[jj]*1e7)
                                    self.uv_vol_uvtot_vol_1_wa.append(uv_vol[jj]/uv_vol_sum)
                                    self.shap_1_wa.append(shapvalues[jj]*1e3)
                                    self.shap_1_vol_wa.append(shapvalues[jj]/uv_struc.vol[jj]*1e9)
                                    self.event_1_wa.append(uv_struc.event[jj])
                                else:
                                    self.volume_1_wd.append(uv_struc.vol[jj]/1e6)
                                    self.uv_uvtot_1_wd.append(uv[jj])
                                    self.uv_uvtot_1_vol_wd.append(uv[jj]/uv_struc.vol[jj]*1e7)
                                    self.uv_vol_uvtot_vol_1_wd.append(uv_vol[jj]/uv_vol_sum)
                                    self.shap_1_wd.append(shapvalues[jj]*1e3)
                                    self.shap_1_vol_wd.append(shapvalues[jj]/uv_struc.vol[jj]*1e9)
                                    self.event_1_wd.append(uv_struc.event[jj])
                            elif uv_struc.event[indexjj] == 2:
                                self.volume_2.append(uv_struc.vol[indexjj]/1e6)
                                self.shap_2.append(shapvalues[jj]*1e3)
                                self.shap_2_vol.append(shapvalues[jj]/uv_struc.vol[indexjj]*1e9)
                                self.event_2.append(uv_struc.event[indexjj])
                                self.uv_uvtot_2.append(uv[jj])
                                self.uv_uvtot_2_vol.append(uv[jj]/uv_struc.vol[indexjj]*1e7)
                                self.uv_vol_uvtot_vol_2.append(uv_vol[jj]/uv_vol_sum)
                                self.dxdy_2.append((uv_struc.dx[indexjj]+1e-10)/(uv_struc.ymax[indexjj]-uv_struc.ymin[indexjj]+1e-5))
                                self.shap2cum += shapvalues[jj]
                                self.shap_vol2cum += shapvalues[jj]/uv_struc.vol[indexjj]
                                self.cdg_y_2.append(uv_struc.cdg_y[indexjj])
                                if yplus_min_ii < 20:
                                    self.volume_2_wa.append(uv_struc.vol[jj]/1e6)
                                    self.uv_uvtot_2_wa.append(uv[jj])
                                    self.uv_uvtot_2_vol_wa.append(uv[jj]/uv_struc.vol[jj]*1e7)
                                    self.uv_vol_uvtot_vol_2_wa.append(uv_vol[jj]/uv_vol_sum)
                                    self.shap_2_wa.append(shapvalues[jj]*1e3)
                                    self.shap_2_vol_wa.append(shapvalues[jj]/uv_struc.vol[jj]*1e9)
                                    self.event_2_wa.append(uv_struc.event[jj])
                                else:
                                    self.volume_2_wd.append(uv_struc.vol[jj]/1e6)
                                    self.uv_uvtot_2_wd.append(uv[jj])
                                    self.uv_uvtot_2_vol_wd.append(uv[jj]/uv_struc.vol[jj]*1e7)
                                    self.uv_vol_uvtot_vol_2_wd.append(uv_vol[jj]/uv_vol_sum)
                                    self.shap_2_wd.append(shapvalues[jj]*1e3)
                                    self.shap_2_vol_wd.append(shapvalues[jj]/uv_struc.vol[jj]*1e9)
                                    self.event_2_wd.append(uv_struc.event[jj])
                            elif uv_struc.event[indexjj] == 3:
                                self.volume_3.append(uv_struc.vol[indexjj]/1e6)
                                self.shap_3.append(shapvalues[jj]*1e3)
                                self.shap_3_vol.append(shapvalues[jj]/uv_struc.vol[indexjj]*1e9)
                                self.event_3.append(uv_struc.event[indexjj])
                                self.uv_uvtot_3.append(uv[jj])
                                self.uv_uvtot_3_vol.append(uv[jj]/uv_struc.vol[indexjj]*1e7)
                                self.uv_vol_uvtot_vol_3.append(uv_vol[jj]/uv_vol_sum)
                                self.dxdy_3.append((uv_struc.dx[indexjj]+1e-10)/(uv_struc.ymax[indexjj]-uv_struc.ymin[indexjj]+1e-5))
                                self.shap3cum += shapvalues[jj]
                                self.shap_vol3cum += shapvalues[jj]/uv_struc.vol[indexjj]
                                self.cdg_y_3.append(uv_struc.cdg_y[indexjj])
                                if yplus_min_ii < 20:
                                    self.volume_3_wa.append(uv_struc.vol[jj]/1e6)
                                    self.uv_uvtot_3_wa.append(uv[jj])
                                    self.uv_uvtot_3_vol_wa.append(uv[jj]/uv_struc.vol[jj]*1e7)
                                    self.uv_vol_uvtot_vol_3_wa.append(uv_vol[jj]/uv_vol_sum)
                                    self.shap_3_wa.append(shapvalues[jj]*1e3)
                                    self.shap_3_vol_wa.append(shapvalues[jj]/uv_struc.vol[jj]*1e9)
                                    self.event_3_wa.append(uv_struc.event[jj])
                                else:
                                    self.volume_3_wd.append(uv_struc.vol[jj]/1e6)
                                    self.uv_uvtot_3_wd.append(uv[jj])
                                    self.uv_uvtot_3_vol_wd.append(uv[jj]/uv_struc.vol[jj]*1e7)
                                    self.uv_vol_uvtot_vol_3_wd.append(uv_vol[jj]/uv_vol_sum)
                                    self.shap_3_wd.append(shapvalues[jj]*1e3)
                                    self.shap_3_vol_wd.append(shapvalues[jj]/uv_struc.vol[jj]*1e9)
                                    self.event_3_wd.append(uv_struc.event[jj])
                            elif uv_struc.event[indexjj] == 4:
                                self.volume_4.append(uv_struc.vol[indexjj]/1e6)
                                self.shap_4.append(shapvalues[jj]*1e3)
                                self.shap_4_vol.append(shapvalues[jj]/uv_struc.vol[indexjj]*1e9)
                                self.event_4.append(uv_struc.event[indexjj])
                                self.uv_uvtot_4.append(uv[jj])
                                self.uv_uvtot_4_vol.append(uv[jj]/uv_struc.vol[indexjj]*1e7)
                                self.uv_vol_uvtot_vol_4.append(uv_vol[jj]/uv_vol_sum) 
                                self.dxdy_4.append((uv_struc.dx[indexjj]+1e-10)/(uv_struc.ymax[indexjj]-uv_struc.ymin[indexjj]+1e-5))
                                self.shap4cum += shapvalues[jj]
                                self.shap_vol4cum += shapvalues[jj]/uv_struc.vol[indexjj]
                                self.cdg_y_4.append(uv_struc.cdg_y[indexjj])
                                if yplus_min_ii < 20:
                                    self.volume_4_wa.append(uv_struc.vol[jj]/1e6)
                                    self.uv_uvtot_4_wa.append(uv[jj])
                                    self.uv_uvtot_4_vol_wa.append(uv[jj]/uv_struc.vol[jj]*1e7)
                                    self.uv_vol_uvtot_vol_4_wa.append(uv_vol[jj]/uv_vol_sum)
                                    self.shap_4_wa.append(shapvalues[jj]*1e3)
                                    self.shap_4_vol_wa.append(shapvalues[jj]/uv_struc.vol[jj]*1e9)
                                    self.event_4_wa.append(uv_struc.event[jj])
                                else:
                                    self.volume_4_wd.append(uv_struc.vol[jj]/1e6)
                                    self.uv_uvtot_4_wd.append(uv[jj])
                                    self.uv_uvtot_4_vol_wd.append(uv[jj]/uv_struc.vol[jj]*1e7)
                                    self.uv_vol_uvtot_vol_4_wd.append(uv_vol[jj]/uv_vol_sum)
                                    self.shap_4_wd.append(shapvalues[jj]*1e3)
                                    self.shap_4_vol_wd.append(shapvalues[jj]/uv_struc.vol[jj]*1e9)
                                    self.event_4_wd.append(uv_struc.event[jj])
                            for ii_arlim1 in np.arange(ngrid):
                                arlim1inf = 10**AR1_vec[ii_arlim1]
                                arlim1sup = 10**AR1_vec[ii_arlim1+1]
                                if AR1 >= arlim1inf and AR1<arlim1sup:
                                    if uv_struc.event[indexjj] == 1:
                                        self.SHAP_grid1[ii_arlim1] +=\
                                        shapvalues[jj]
                                        self.SHAP_grid1vol[ii_arlim1] +=\
                                        shapvalues[jj]/uv_struc.vol[indexjj]
                                        self.npoin1[ii_arlim1] += 1 
                                    elif uv_struc.event[indexjj] == 2:
                                        self.SHAP_grid2[ii_arlim1] +=\
                                        shapvalues[jj]
                                        self.SHAP_grid2vol[ii_arlim1] +=\
                                        shapvalues[jj]/uv_struc.vol[indexjj]
                                        self.npoin2[ii_arlim1] += 1 
                                    elif uv_struc.event[indexjj] == 3:
                                        self.SHAP_grid3[ii_arlim1] +=\
                                        shapvalues[jj]
                                        self.SHAP_grid3vol[ii_arlim1] +=\
                                        shapvalues[jj]/uv_struc.vol[indexjj]
                                        self.npoin3[ii_arlim1] += 1 
                                    elif uv_struc.event[indexjj] == 4:
                                        self.SHAP_grid4[ii_arlim1] +=\
                                        shapvalues[jj]
                                        self.SHAP_grid4vol[ii_arlim1] +=\
                                        shapvalues[jj]/uv_struc.vol[indexjj]
                                        self.npoin4[ii_arlim1] += 1 
                    vol_b = np.sum(normdata.vol)-np.sum(uv_struc.vol)
                    self.shapbcum += shapvalues[-1]
                    self.shap_volbcum += shapvalues[-1]/vol_b
                    self.shapback_list.append(shapback)
                    volback = np.sum(normdata.vol)-np.sum(uv_struc.vol)
                    self.shapbackvol_list.append(shapback/volback)
                    numfield += 1
                except:
                    print('Missing: '+file+str(ii)+'.h5.shap')
                if saveuv:
                    import h5py
                    hf = h5py.File(filereystress_ii, 'w')
                    hf.create_dataset('uv', data=uv)
            for ii_arlim1 in np.arange(ngrid):
                if self.npoin1[ii_arlim1] == 0:
                    self.SHAP_grid1[ii_arlim1] = np.nan
                    self.SHAP_grid1vol[ii_arlim1] = np.nan
                else:
                    self.SHAP_grid1[ii_arlim1] /= self.npoin1[ii_arlim1]
                    self.SHAP_grid1vol[ii_arlim1] /= self.npoin1[ii_arlim1]
                if self.npoin2[ii_arlim1] == 0:
                    self.SHAP_grid2[ii_arlim1] = np.nan
                    self.SHAP_grid2vol[ii_arlim1] = np.nan
                else:
                    self.SHAP_grid2[ii_arlim1] /= self.npoin2[ii_arlim1]
                    self.SHAP_grid2vol[ii_arlim1] /= self.npoin2[ii_arlim1]
                if self.npoin3[ii_arlim1] == 0:
                    self.SHAP_grid3[ii_arlim1] = np.nan
                    self.SHAP_grid3vol[ii_arlim1] = np.nan
                else:
                    self.SHAP_grid3[ii_arlim1] /= self.npoin3[ii_arlim1]
                    self.SHAP_grid3vol[ii_arlim1] /= self.npoin3[ii_arlim1]
                if self.npoin4[ii_arlim1] == 0:
                    self.SHAP_grid4[ii_arlim1] = np.nan
                    self.SHAP_grid4vol[ii_arlim1] = np.nan
                else:
                    self.SHAP_grid4[ii_arlim1] /= self.npoin4[ii_arlim1]
                    self.SHAP_grid4vol[ii_arlim1] /= self.npoin4[ii_arlim1]
                    
    
                    
                    
            shapback_mean = np.mean(self.shapback_list)
            shapback_std = np.std(self.shapback_list)
            shapbackvol_mean = np.mean(self.shapbackvol_list)
            shapbackvol_std = np.std(self.shapbackvol_list)
            file_save = open('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/backSHAP.txt', "w+") 
            file_save.write('Mean: '+str(shapback_mean)+\
                            '\Std: '+str(shapback_std)+'\n')
            file_save.write('Mean: '+str(shapbackvol_mean)+\
                            '\Std: '+str(shapbackvol_std)+'\n')
            file_save.close()
            hf = h5py.File(fileread, 'w')
            hf.create_dataset('volume_wa', data=self.volume_wa)
            hf.create_dataset('volume_wd', data=self.volume_wd)
            hf.create_dataset('shap_wa', data=self.shap_wa)
            hf.create_dataset('shap_wd', data=self.shap_wd)
            hf.create_dataset('shap_wa_vol', data=self.shap_wa_vol)
            hf.create_dataset('shap_wd_vol', data=self.shap_wd_vol)
            hf.create_dataset('event_wa', data=self.event_wa)
            hf.create_dataset('event_wd', data=self.event_wd)
            hf.create_dataset('uv_uvtot_wa', data=self.uv_uvtot_wa)
            hf.create_dataset('uv_uvtot_wd', data=self.uv_uvtot_wd)
            hf.create_dataset('uv_uvtot_wa_vol', data=self.uv_uvtot_wa_vol)
            hf.create_dataset('uv_uvtot_wd_vol', data=self.uv_uvtot_wd_vol)
            hf.create_dataset('uv_vol_uvtot_vol_wa', data=self.uv_vol_uvtot_vol_wa)
            hf.create_dataset('uv_vol_uvtot_vol_wd', data=self.uv_vol_uvtot_vol_wd)
            hf.create_dataset('volume_1', data=self.volume_1)
            hf.create_dataset('volume_2', data=self.volume_2)
            hf.create_dataset('volume_3', data=self.volume_3)
            hf.create_dataset('volume_4', data=self.volume_4)
            hf.create_dataset('shap_1', data=self.shap_1)
            hf.create_dataset('shap_2', data=self.shap_2)
            hf.create_dataset('shap_3', data=self.shap_3)
            hf.create_dataset('shap_4', data=self.shap_4)
            hf.create_dataset('shap_1_vol', data=self.shap_1_vol)
            hf.create_dataset('shap_2_vol', data=self.shap_2_vol)
            hf.create_dataset('shap_3_vol', data=self.shap_3_vol)
            hf.create_dataset('shap_4_vol', data=self.shap_4_vol)
            hf.create_dataset('uv_uvtot_1', data=self.uv_uvtot_1)
            hf.create_dataset('uv_uvtot_2', data=self.uv_uvtot_2)
            hf.create_dataset('uv_uvtot_3', data=self.uv_uvtot_3)
            hf.create_dataset('uv_uvtot_4', data=self.uv_uvtot_4)
            hf.create_dataset('uv_uvtot_1_vol', data=self.uv_uvtot_1_vol)
            hf.create_dataset('uv_uvtot_2_vol', data=self.uv_uvtot_2_vol)
            hf.create_dataset('uv_uvtot_3_vol', data=self.uv_uvtot_3_vol)
            hf.create_dataset('uv_uvtot_4_vol', data=self.uv_uvtot_4_vol)
            hf.create_dataset('uv_vol_uvtot_vol_1', data=self.uv_vol_uvtot_vol_1)
            hf.create_dataset('uv_vol_uvtot_vol_2', data=self.uv_vol_uvtot_vol_2)
            hf.create_dataset('uv_vol_uvtot_vol_3', data=self.uv_vol_uvtot_vol_3)
            hf.create_dataset('uv_vol_uvtot_vol_4', data=self.uv_vol_uvtot_vol_4)
            hf.create_dataset('event_1', data=self.event_1)
            hf.create_dataset('event_2', data=self.event_2)
            hf.create_dataset('event_3', data=self.event_3)
            hf.create_dataset('event_4', data=self.event_4)
            hf.create_dataset('volume_1_wa', data=self.volume_1_wa)
            hf.create_dataset('volume_2_wa', data=self.volume_2_wa)
            hf.create_dataset('volume_3_wa', data=self.volume_3_wa)
            hf.create_dataset('volume_4_wa', data=self.volume_4_wa)
            hf.create_dataset('shap_1_wa', data=self.shap_1_wa)
            hf.create_dataset('shap_2_wa', data=self.shap_2_wa)
            hf.create_dataset('shap_3_wa', data=self.shap_3_wa)
            hf.create_dataset('shap_4_wa', data=self.shap_4_wa)
            hf.create_dataset('shap_1_vol_wa', data=self.shap_1_vol_wa)
            hf.create_dataset('shap_2_vol_wa', data=self.shap_2_vol_wa)
            hf.create_dataset('shap_3_vol_wa', data=self.shap_3_vol_wa)
            hf.create_dataset('shap_4_vol_wa', data=self.shap_4_vol_wa)
            hf.create_dataset('uv_uvtot_1_wa', data=self.uv_uvtot_1_wa)
            hf.create_dataset('uv_uvtot_2_wa', data=self.uv_uvtot_2_wa)
            hf.create_dataset('uv_uvtot_3_wa', data=self.uv_uvtot_3_wa)
            hf.create_dataset('uv_uvtot_4_wa', data=self.uv_uvtot_4_wa)
            hf.create_dataset('uv_uvtot_1_vol_wa', data=self.uv_uvtot_1_vol_wa)
            hf.create_dataset('uv_uvtot_2_vol_wa', data=self.uv_uvtot_2_vol_wa)
            hf.create_dataset('uv_uvtot_3_vol_wa', data=self.uv_uvtot_3_vol_wa)
            hf.create_dataset('uv_uvtot_4_vol_wa', data=self.uv_uvtot_4_vol_wa)
            hf.create_dataset('uv_vol_uvtot_vol_1_wa', data=self.uv_vol_uvtot_vol_1_wa)
            hf.create_dataset('uv_vol_uvtot_vol_2_wa', data=self.uv_vol_uvtot_vol_2_wa)
            hf.create_dataset('uv_vol_uvtot_vol_3_wa', data=self.uv_vol_uvtot_vol_3_wa)
            hf.create_dataset('uv_vol_uvtot_vol_4_wa', data=self.uv_vol_uvtot_vol_4_wa)
            hf.create_dataset('event_1_wa', data=self.event_1_wa)
            hf.create_dataset('event_2_wa', data=self.event_2_wa)
            hf.create_dataset('event_3_wa', data=self.event_3_wa)
            hf.create_dataset('event_4_wa', data=self.event_4_wa)
            hf.create_dataset('volume_1_wd', data=self.volume_1_wd)
            hf.create_dataset('volume_2_wd', data=self.volume_2_wd)
            hf.create_dataset('volume_3_wd', data=self.volume_3_wd)
            hf.create_dataset('volume_4_wd', data=self.volume_4_wd)
            hf.create_dataset('shap_1_wd', data=self.shap_1_wd)
            hf.create_dataset('shap_2_wd', data=self.shap_2_wd)
            hf.create_dataset('shap_3_wd', data=self.shap_3_wd)
            hf.create_dataset('shap_4_wd', data=self.shap_4_wd)
            hf.create_dataset('shap_1_vol_wd', data=self.shap_1_vol_wd)
            hf.create_dataset('shap_2_vol_wd', data=self.shap_2_vol_wd)
            hf.create_dataset('shap_3_vol_wd', data=self.shap_3_vol_wd)
            hf.create_dataset('shap_4_vol_wd', data=self.shap_4_vol_wd)
            hf.create_dataset('uv_uvtot_1_wd', data=self.uv_uvtot_1_wd)
            hf.create_dataset('uv_uvtot_2_wd', data=self.uv_uvtot_2_wd)
            hf.create_dataset('uv_uvtot_3_wd', data=self.uv_uvtot_3_wd)
            hf.create_dataset('uv_uvtot_4_wd', data=self.uv_uvtot_4_wd)
            hf.create_dataset('uv_uvtot_1_vol_wd', data=self.uv_uvtot_1_vol_wd)
            hf.create_dataset('uv_uvtot_2_vol_wd', data=self.uv_uvtot_2_vol_wd)
            hf.create_dataset('uv_uvtot_3_vol_wd', data=self.uv_uvtot_3_vol_wd)
            hf.create_dataset('uv_uvtot_4_vol_wd', data=self.uv_uvtot_4_vol_wd)
            hf.create_dataset('uv_vol_uvtot_vol_1_wd', data=self.uv_vol_uvtot_vol_1_wd)
            hf.create_dataset('uv_vol_uvtot_vol_2_wd', data=self.uv_vol_uvtot_vol_2_wd)
            hf.create_dataset('uv_vol_uvtot_vol_3_wd', data=self.uv_vol_uvtot_vol_3_wd)
            hf.create_dataset('uv_vol_uvtot_vol_4_wd', data=self.uv_vol_uvtot_vol_4_wd)
            hf.create_dataset('event_1_wd', data=self.event_1_wd)
            hf.create_dataset('event_2_wd', data=self.event_2_wd)
            hf.create_dataset('event_3_wd', data=self.event_3_wd)
            hf.create_dataset('event_4_wd', data=self.event_4_wd)
            hf.create_dataset('voltot', data=self.voltot)
            hf.create_dataset('shapback_list', data=self.shapback_list)
            hf.create_dataset('shapbackvol_list', data=self.shapbackvol_list)
            hf.create_dataset('AR1_grid', data=self.AR1_grid)
            hf.create_dataset('SHAP_grid1', data=self.SHAP_grid1)
            hf.create_dataset('SHAP_grid2', data=self.SHAP_grid2)
            hf.create_dataset('SHAP_grid3', data=self.SHAP_grid3)
            hf.create_dataset('SHAP_grid4', data=self.SHAP_grid4)
            hf.create_dataset('SHAP_grid1vol', data=self.SHAP_grid1vol)
            hf.create_dataset('SHAP_grid2vol', data=self.SHAP_grid2vol)
            hf.create_dataset('SHAP_grid3vol', data=self.SHAP_grid3vol)
            hf.create_dataset('SHAP_grid4vol', data=self.SHAP_grid4vol)
            hf.create_dataset('npoin1', data=self.npoin1)
            hf.create_dataset('npoin2', data=self.npoin2)
            hf.create_dataset('npoin3', data=self.npoin3)
            hf.create_dataset('npoin4', data=self.npoin4)
            hf.create_dataset('shap1cum', data=self.shap1cum)
            hf.create_dataset('shap2cum', data=self.shap2cum)
            hf.create_dataset('shap3cum', data=self.shap3cum)
            hf.create_dataset('shap4cum', data=self.shap4cum)
            hf.create_dataset('shapbcum', data=self.shapbcum)
            hf.create_dataset('shap_vol1cum', data=self.shap_vol1cum)
            hf.create_dataset('shap_vol2cum', data=self.shap_vol2cum)
            hf.create_dataset('shap_vol3cum', data=self.shap_vol3cum)
            hf.create_dataset('shap_vol4cum', data=self.shap_vol4cum)
            hf.create_dataset('shap_volbcum', data=self.shap_volbcum)
            hf.create_dataset('shapmax', data=self.shapmax)
            hf.create_dataset('shapmin', data=self.shapmin)
            hf.create_dataset('shapmaxvol', data=self.shapmaxvol)
            hf.create_dataset('shapminvol', data=self.shapminvol)
            hf.create_dataset('cdg_y_1', data=self.cdg_y_1)
            hf.create_dataset('cdg_y_2', data=self.cdg_y_2)
            hf.create_dataset('cdg_y_3', data=self.cdg_y_3)
            hf.create_dataset('cdg_y_4', data=self.cdg_y_4)
            hf.create_dataset('cdg_y_wa', data=self.cdg_y_wa)
            hf.create_dataset('cdg_y_wd', data=self.cdg_y_wd)
            hf.create_dataset('dxdy_wa', data=self.dxdy_wa)
            hf.create_dataset('dxdy_wd', data=self.dxdy_wd)
            hf.create_dataset('dxdy_1', data=self.dxdy_1)
            hf.create_dataset('dxdy_2', data=self.dxdy_2)
            hf.create_dataset('dxdy_3', data=self.dxdy_3)
            hf.create_dataset('dxdy_4', data=self.dxdy_4)
            hf.close()   
        
    def plot_shaps(self,colormap='viridis'):
        """ 
        Function for plotting the results of the SHAP vs the volume
        """
        import matplotlib.pyplot as plt
        import matplotlib as mpl
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/')
        except:
            pass
        fs = 20
        fig = plt.figure()
        ax = plt.axes()
        if self.wallattach:
            plt.scatter(self.volume_wa,self.shap_wa,c=self.event_wa,marker='o',\
                        linewidths=0.5,edgecolors='black',s=100,\
                        cmap=plt.cm.get_cmap(colormap,4),vmin=1,vmax=4)
        plt.scatter(self.volume_wd,self.shap_wd,c=self.event_wd,marker='s',\
                    linewidths=0.5,edgecolors='black',s=100,\
                    cmap=plt.cm.get_cmap(colormap,4),vmin=1,vmax=4)
        plt.grid()
        plt.xlabel('$S^+ \cdot 10^6$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        handles = [mpl.lines.Line2D([0],[0],marker='o',markerfacecolor='w',\
                                    markeredgecolor='k',markersize=1, ls=''),\
                   mpl.lines.Line2D([0],[0],marker='s',markerfacecolor='w',\
                                    markeredgecolor='k',markersize=1, ls='')]
        labels= ['W-A','W-D']
        if self.wallattach:
            plt.legend(handles,labels,fontsize=fs,markerscale=10) 
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(ticks=[1,2,3,4],cax = cbaxes)
        cb.ax.set_yticklabels(['Outward\ninteraction','Ejection',\
                               'Inward\ninteraction','Sweep'],fontsize=fs-4)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/vol_SHAP_'+colormap+'_30+.png')
        fig = plt.figure()
        ax = plt.axes()
        if self.wallattach:
            plt.scatter(self.volume_wa,self.shap_wa_vol,c=self.event_wa,marker='o',\
                        linewidths=0.5,edgecolors='black',s=100,\
                        cmap=plt.cm.get_cmap(colormap,4),vmin=1,vmax=4)
        plt.scatter(self.volume_wd,self.shap_wd_vol,c=self.event_wd,marker='s',\
                    linewidths=0.5,edgecolors='black',s=100,\
                    cmap=plt.cm.get_cmap(colormap,4),vmin=1,vmax=4)
        plt.grid()
        plt.xlabel('$S^+ \cdot 10^6$',fontsize=fs)
        plt.ylabel(self.ylabel_shap_vol,fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        handles = [mpl.lines.Line2D([0],[0],marker='o',markerfacecolor='w',\
                                    markeredgecolor='k',markersize=1, ls=''),\
                   mpl.lines.Line2D([0],[0],marker='s',markerfacecolor='w',\
                                    markeredgecolor='k',markersize=1, ls='')]
        labels= ['W-A','W-D']
        if self.wallattach:
            plt.legend(handles,labels,fontsize=fs,markerscale=10) 
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(ticks=[1,2,3,4],cax = cbaxes)
        cb.ax.set_yticklabels(['Outward\ninteraction','Ejection',\
                               'Inward\ninteraction','Sweep'],fontsize=fs-4)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/vol_SHAPvol_'+colormap+'_30+.png')
        
        
        
        
                
    def plot_shaps_pdf(self,colormap='viridis',bin_num=50,lev_val=5,alf=0.5):
        """ 
        Function for plotting the results of the SHAP vs the Reynolds stress
        """
        
        import matplotlib.pyplot as plt
        import matplotlib as mpl    
        from scipy.interpolate import interp2d
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/')
        except:
            pass
        xhistmin = np.min([np.min(self.volume_1),np.min(self.volume_2),np.min(self.volume_3),np.min(self.volume_4)])/1.2
        xhistmax = np.max([np.max(self.volume_1),np.max(self.volume_2),np.max(self.volume_3),np.max(self.volume_4)])*1.2
        yhistmin = np.min([np.min(self.shap_1),np.min(self.shap_2),np.min(self.shap_3),np.min(self.shap_4)])/1.2
        yhistmax = np.max([np.max(self.shap_1),np.max(self.shap_2),np.max(self.shap_3),np.max(self.shap_4)])*1.2
        histogram1,vol_value1,shap_value1 = np.histogram2d(self.volume_1,self.shap_1,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram2,vol_value2,shap_value2 = np.histogram2d(self.volume_2,self.shap_2,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram3,vol_value3,shap_value3 = np.histogram2d(self.volume_3,self.shap_3,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram4,vol_value4,shap_value4 = np.histogram2d(self.volume_4,self.shap_4,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        vol_value1 = vol_value1[:-1]+np.diff(vol_value1)/2
        shap_value1 = shap_value1[:-1]+np.diff(shap_value1)/2
        vol_value2 = vol_value2[:-1]+np.diff(vol_value2)/2
        shap_value2 = shap_value2[:-1]+np.diff(shap_value2)/2
        vol_value3 = vol_value3[:-1]+np.diff(vol_value3)/2
        shap_value3 = shap_value3[:-1]+np.diff(shap_value3)/2
        vol_value4 = vol_value4[:-1]+np.diff(vol_value4)/2
        shap_value4 = shap_value4[:-1]+np.diff(shap_value4)/2
        min_vol = np.min([vol_value1,vol_value2,vol_value3,vol_value4])
        max_vol = np.max([vol_value1,vol_value2,vol_value3,vol_value4])
        min_shap = np.min([shap_value1,shap_value2,shap_value3,shap_value4])
        max_shap = np.max([shap_value1,shap_value2,shap_value3,shap_value4])
        interp_h1 = interp2d(vol_value1,shap_value1,histogram1)
        interp_h2 = interp2d(vol_value2,shap_value2,histogram2)
        interp_h3 = interp2d(vol_value3,shap_value3,histogram3)
        interp_h4 = interp2d(vol_value4,shap_value4,histogram4)
        vec_vol = np.linspace(min_vol,max_vol,1000)
        vec_shap = np.linspace(min_shap,max_shap,1000)
        vol_grid,shap_grid = np.meshgrid(vec_vol,vec_shap)
        histogram_Q1 = interp_h1(vec_vol,vec_shap)
        histogram_Q2 = interp_h2(vec_vol,vec_shap)
        histogram_Q3 = interp_h3(vec_vol,vec_shap)
        histogram_Q4 = interp_h4(vec_vol,vec_shap)
        fs = 20
        plt.figure()
        color11 = plt.cm.get_cmap(colormap,4).colors[0,0]
        color12 = plt.cm.get_cmap(colormap,4).colors[0,1]
        color13 = plt.cm.get_cmap(colormap,4).colors[0,2]
        color21 = plt.cm.get_cmap(colormap,4).colors[1,0]
        color22 = plt.cm.get_cmap(colormap,4).colors[1,1]
        color23 = plt.cm.get_cmap(colormap,4).colors[1,2]
        color31 = plt.cm.get_cmap(colormap,4).colors[2,0]
        color32 = plt.cm.get_cmap(colormap,4).colors[2,1]
        color33 = plt.cm.get_cmap(colormap,4).colors[2,2]
        color41 = plt.cm.get_cmap(colormap,4).colors[3,0]
        color42 = plt.cm.get_cmap(colormap,4).colors[3,1]
        color43 = plt.cm.get_cmap(colormap,4).colors[3,2]
        plt.contourf(vol_grid,shap_grid,histogram_Q1.T,levels=[lev_val,1e5*lev_val],colors=[(color11,color12,color13)],alpha=alf)
        plt.contourf(vol_grid,shap_grid,histogram_Q2.T,levels=[lev_val,1e5*lev_val],colors=[(color21,color22,color23)],alpha=alf)
        plt.contourf(vol_grid,shap_grid,histogram_Q3.T,levels=[lev_val,1e5*lev_val],colors=[(color31,color32,color33)],alpha=alf)
        plt.contourf(vol_grid,shap_grid,histogram_Q4.T,levels=[lev_val,1e5*lev_val],colors=[(color41,color42,color43)],alpha=alf)
        plt.contour(vol_grid,shap_grid,histogram_Q1.T,levels=[lev_val],colors=[(color11,color12,color13)])
        plt.contour(vol_grid,shap_grid,histogram_Q2.T,levels=[lev_val],colors=[(color21,color22,color23)])
        plt.contour(vol_grid,shap_grid,histogram_Q3.T,levels=[lev_val],colors=[(color31,color32,color33)])
        plt.contour(vol_grid,shap_grid,histogram_Q4.T,levels=[lev_val],colors=[(color41,color42,color43)])
        plt.xlim([0,3])
        plt.ylim([0,30])
        plt.grid()
        plt.xlabel('$S^+ \cdot 10^6$',\
                   fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        handles = [mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color11,color12,color13,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color11,color12,color13,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color21,color22,color23,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color21,color22,color23,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color31,color32,color33,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color31,color32,color33,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color41,color42,color43,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color41,color42,color43,alf))]
        labels= ['Outward\ninteractions','Ejections','Inward\ninteractions','Sweeps']
        plt.legend(handles,labels,fontsize=fs-4,loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_vol_SHAP_'+colormap+'_30+.png')
        xhistmin = np.min([np.min(self.volume_1),np.min(self.volume_2),np.min(self.volume_3),np.min(self.volume_4)])/1.2
        xhistmax = np.max([np.max(self.volume_1),np.max(self.volume_2),np.max(self.volume_3),np.max(self.volume_4)])*1.2
        yhistmin = np.min([np.min(self.shap_1_vol),np.min(self.shap_2_vol),np.min(self.shap_3_vol),np.min(self.shap_4_vol)])/1.2
        yhistmax = np.max([np.max(self.shap_1_vol),np.max(self.shap_2_vol),np.max(self.shap_3_vol),np.max(self.shap_4_vol)])*1.2
        histogram1_vol,vol_value1_vol,shap_value1_vol = np.histogram2d(self.volume_1,self.shap_1_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram2_vol,vol_value2_vol,shap_value2_vol = np.histogram2d(self.volume_2,self.shap_2_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram3_vol,vol_value3_vol,shap_value3_vol = np.histogram2d(self.volume_3,self.shap_3_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram4_vol,vol_value4_vol,shap_value4_vol = np.histogram2d(self.volume_4,self.shap_4_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        vol_value1_vol = vol_value1_vol[:-1]+np.diff(vol_value1_vol)/2
        shap_value1_vol = shap_value1_vol[:-1]+np.diff(shap_value1_vol)/2
        vol_value2_vol = vol_value2_vol[:-1]+np.diff(vol_value2_vol)/2
        shap_value2_vol = shap_value2_vol[:-1]+np.diff(shap_value2_vol)/2
        vol_value3_vol = vol_value3_vol[:-1]+np.diff(vol_value3_vol)/2
        shap_value3_vol = shap_value3_vol[:-1]+np.diff(shap_value3_vol)/2
        vol_value4_vol = vol_value4_vol[:-1]+np.diff(vol_value4_vol)/2
        shap_value4_vol = shap_value4_vol[:-1]+np.diff(shap_value4_vol)/2
        min_vol_vol = np.min([vol_value1_vol,vol_value2_vol,vol_value3_vol,vol_value4_vol])
        max_vol_vol = np.max([vol_value1_vol,vol_value2_vol,vol_value3_vol,vol_value4_vol])
        min_shap_vol = np.min([shap_value1_vol,shap_value2_vol,shap_value3_vol,shap_value4_vol])
        max_shap_vol = np.max([shap_value1_vol,shap_value2_vol,shap_value3_vol,shap_value4_vol])
        interp_h1_vol = interp2d(vol_value1_vol,shap_value1_vol,histogram1_vol)
        interp_h2_vol = interp2d(vol_value2_vol,shap_value2_vol,histogram2_vol)
        interp_h3_vol = interp2d(vol_value3_vol,shap_value3_vol,histogram3_vol)
        interp_h4_vol = interp2d(vol_value4_vol,shap_value4_vol,histogram4_vol)
        vec_vol_vol = np.linspace(min_vol_vol,max_vol_vol,1000)
        vec_shap_vol = np.linspace(min_shap_vol,max_shap_vol,1000)
        vol_grid_vol,shap_grid_vol = np.meshgrid(vec_vol_vol,vec_shap_vol)
        histogram_Q1_vol = interp_h1_vol(vec_vol_vol,vec_shap_vol)
        histogram_Q2_vol = interp_h2_vol(vec_vol_vol,vec_shap_vol)
        histogram_Q3_vol = interp_h3_vol(vec_vol_vol,vec_shap_vol)
        histogram_Q4_vol = interp_h4_vol(vec_vol_vol,vec_shap_vol)
        fs = 20
        plt.figure()
        color11 = plt.cm.get_cmap(colormap,4).colors[0,0]
        color12 = plt.cm.get_cmap(colormap,4).colors[0,1]
        color13 = plt.cm.get_cmap(colormap,4).colors[0,2]
        color21 = plt.cm.get_cmap(colormap,4).colors[1,0]
        color22 = plt.cm.get_cmap(colormap,4).colors[1,1]
        color23 = plt.cm.get_cmap(colormap,4).colors[1,2]
        color31 = plt.cm.get_cmap(colormap,4).colors[2,0]
        color32 = plt.cm.get_cmap(colormap,4).colors[2,1]
        color33 = plt.cm.get_cmap(colormap,4).colors[2,2]
        color41 = plt.cm.get_cmap(colormap,4).colors[3,0]
        color42 = plt.cm.get_cmap(colormap,4).colors[3,1]
        color43 = plt.cm.get_cmap(colormap,4).colors[3,2]
        plt.contourf(vol_grid_vol,shap_grid_vol,histogram_Q1_vol.T,levels=[lev_val,1e5*lev_val],colors=[(color11,color12,color13)],alpha=alf)
        plt.contourf(vol_grid_vol,shap_grid_vol,histogram_Q2_vol.T,levels=[lev_val,1e5*lev_val],colors=[(color21,color22,color23)],alpha=alf)
        plt.contourf(vol_grid_vol,shap_grid_vol,histogram_Q3_vol.T,levels=[lev_val,1e5*lev_val],colors=[(color31,color32,color33)],alpha=alf)
        plt.contourf(vol_grid_vol,shap_grid_vol,histogram_Q4_vol.T,levels=[lev_val,1e5*lev_val],colors=[(color41,color42,color43)],alpha=alf)
        plt.contour(vol_grid_vol,shap_grid_vol,histogram_Q1_vol.T,levels=[lev_val],colors=[(color11,color12,color13)])
        plt.contour(vol_grid_vol,shap_grid_vol,histogram_Q2_vol.T,levels=[lev_val],colors=[(color21,color22,color23)])
        plt.contour(vol_grid_vol,shap_grid_vol,histogram_Q3_vol.T,levels=[lev_val],colors=[(color31,color32,color33)])
        plt.contour(vol_grid_vol,shap_grid_vol,histogram_Q4_vol.T,levels=[lev_val],colors=[(color41,color42,color43)])
        plt.grid()
        plt.xlim([0,3])
        plt.ylim([0,40])
        plt.xlabel('$S^+ \cdot 10^6$',\
                   fontsize=fs)
        plt.ylabel(self.ylabel_shap_vol,fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        handles = [mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color11,color12,color13,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color11,color12,color13,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color21,color22,color23,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color21,color22,color23,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color31,color32,color33,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color31,color32,color33,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color41,color42,color43,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color41,color42,color43,alf))]
        labels= ['Outward\ninteractions','Ejections','Inward\ninteractions','Sweeps']
        plt.legend(handles,labels,fontsize=fs-4,loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_vol_SHAPvol_'+colormap+'_30+.png')
        
        
                      
    def plot_shaps_pdf_probability(self,colormap='viridis',bin_num=100,lev_val=2.5,alf=0.5):
        """ 
        Function for plotting the results of the SHAP vs the Reynolds stress
        """
        import matplotlib.pyplot as plt
        import matplotlib as mpl    
        from scipy.interpolate import interp2d
        import matplotlib.colors as colors
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/')
        except:
            pass
        xhistmin = np.min([np.min(self.volume_1),np.min(self.volume_2),np.min(self.volume_3),np.min(self.volume_4)])/1.2
        xhistmax = np.max([np.max(self.volume_1),np.max(self.volume_2),np.max(self.volume_3),np.max(self.volume_4)])*1.2
        yhistmin = np.min([np.min(self.shap_1),np.min(self.shap_2),np.min(self.shap_3),np.min(self.shap_4)])/1.2
        yhistmax = np.max([np.max(self.shap_1),np.max(self.shap_2),np.max(self.shap_3),np.max(self.shap_4)])*1.2
        histogram1,vol_value1,shap_value1 = np.histogram2d(self.volume_1,self.shap_1,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram2,vol_value2,shap_value2 = np.histogram2d(self.volume_2,self.shap_2,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram3,vol_value3,shap_value3 = np.histogram2d(self.volume_3,self.shap_3,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram4,vol_value4,shap_value4 = np.histogram2d(self.volume_4,self.shap_4,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        vol_value1 = vol_value1[:-1]+np.diff(vol_value1)/2
        shap_value1 = shap_value1[:-1]+np.diff(shap_value1)/2
        vol_value2 = vol_value2[:-1]+np.diff(vol_value2)/2
        shap_value2 = shap_value2[:-1]+np.diff(shap_value2)/2
        vol_value3 = vol_value3[:-1]+np.diff(vol_value3)/2
        shap_value3 = shap_value3[:-1]+np.diff(shap_value3)/2
        vol_value4 = vol_value4[:-1]+np.diff(vol_value4)/2
        shap_value4 = shap_value4[:-1]+np.diff(shap_value4)/2
        min_vol = np.min([vol_value1,vol_value2,vol_value3,vol_value4])
        max_vol = np.max([vol_value1,vol_value2,vol_value3,vol_value4])
        min_shap = np.min([shap_value1,shap_value2,shap_value3,shap_value4])
        max_shap = np.max([shap_value1,shap_value2,shap_value3,shap_value4])
        interp_h1 = interp2d(vol_value1,shap_value1,histogram1)
        interp_h2 = interp2d(vol_value2,shap_value2,histogram2)
        interp_h3 = interp2d(vol_value3,shap_value3,histogram3)
        interp_h4 = interp2d(vol_value4,shap_value4,histogram4)
        vec_vol = np.linspace(min_vol,max_vol,1000)
        vec_shap = np.linspace(min_shap,max_shap,1000)
        vol_grid,shap_grid = np.meshgrid(vec_vol,vec_shap)
        histogram_Q1 = interp_h1(vec_vol,vec_shap)
        histogram_Q2 = interp_h2(vec_vol,vec_shap)
        histogram_Q3 = interp_h3(vec_vol,vec_shap)
        histogram_Q4 = interp_h4(vec_vol,vec_shap)
        histogram_Q1[histogram_Q1<3] = 0
        histogram_Q2[histogram_Q2<3] = 0
        histogram_Q3[histogram_Q3<3] = 0
        histogram_Q4[histogram_Q4<3] = 0
        histogram_Q1 /= np.max(histogram_Q1)
        histogram_Q2 /= np.max(histogram_Q2)
        histogram_Q3 /= np.max(histogram_Q3)
        histogram_Q4 /= np.max(histogram_Q4)
        fs = 20
        xmin = 0
        xmax = 3
        ymin = 0
        ymax = 30      
        fig=plt.figure()
        ax = plt.axes()
        plt.pcolor(vol_grid,shap_grid,histogram_Q1.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$S^+\cdot10^6$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_vol_SHAP_'+colormap+'_30+_Q1.png')
        fig=plt.figure()
        ax = plt.axes()
        plt.pcolor(vol_grid,shap_grid,histogram_Q2.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$S^+\cdot10^6$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_vol_SHAP_'+colormap+'_30+_Q2.png')
        fig=plt.figure()
        ax = plt.axes()
        plt.pcolor(vol_grid,shap_grid,histogram_Q3.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$S^+\cdot10^6$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_vol_SHAP_'+colormap+'_30+_Q3.png')
        fig=plt.figure()
        ax = plt.axes()
        plt.pcolor(vol_grid,shap_grid,histogram_Q4.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$S^+\cdot10^6$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_vol_SHAP_'+colormap+'_30+_Q4.png')
        
        
        xhistmin = np.min([np.min(self.volume_1),np.min(self.volume_2),np.min(self.volume_3),np.min(self.volume_4)])/1.2
        xhistmax = np.max([np.max(self.volume_1),np.max(self.volume_2),np.max(self.volume_3),np.max(self.volume_4)])*1.2
        yhistmin = np.min([np.min(self.shap_1_vol),np.min(self.shap_2_vol),np.min(self.shap_3_vol),np.min(self.shap_4_vol)])/1.2
        yhistmax = np.max([np.max(self.shap_1_vol),np.max(self.shap_2_vol),np.max(self.shap_3_vol),np.max(self.shap_4_vol)])*1.2
        histogram1_vol,vol_value1_vol,shap_value1_vol = np.histogram2d(self.volume_1,self.shap_1_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram2_vol,vol_value2_vol,shap_value2_vol = np.histogram2d(self.volume_2,self.shap_2_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram3_vol,vol_value3_vol,shap_value3_vol = np.histogram2d(self.volume_3,self.shap_3_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram4_vol,vol_value4_vol,shap_value4_vol = np.histogram2d(self.volume_4,self.shap_4_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        vol_value1_vol = vol_value1_vol[:-1]+np.diff(vol_value1_vol)/2
        shap_value1_vol = shap_value1_vol[:-1]+np.diff(shap_value1_vol)/2
        vol_value2_vol = vol_value2_vol[:-1]+np.diff(vol_value2_vol)/2
        shap_value2_vol = shap_value2_vol[:-1]+np.diff(shap_value2_vol)/2
        vol_value3_vol = vol_value3_vol[:-1]+np.diff(vol_value3_vol)/2
        shap_value3_vol = shap_value3_vol[:-1]+np.diff(shap_value3_vol)/2
        vol_value4_vol = vol_value4_vol[:-1]+np.diff(vol_value4_vol)/2
        shap_value4_vol = shap_value4_vol[:-1]+np.diff(shap_value4_vol)/2
        min_vol_vol = np.min([vol_value1_vol,vol_value2_vol,vol_value3_vol,vol_value4_vol])
        max_vol_vol = np.max([vol_value1_vol,vol_value2_vol,vol_value3_vol,vol_value4_vol])
        min_shap_vol = np.min([shap_value1_vol,shap_value2_vol,shap_value3_vol,shap_value4_vol])
        max_shap_vol = np.max([shap_value1_vol,shap_value2_vol,shap_value3_vol,shap_value4_vol])
        interp_h1_vol = interp2d(vol_value1_vol,shap_value1_vol,histogram1_vol)
        interp_h2_vol = interp2d(vol_value2_vol,shap_value2_vol,histogram2_vol)
        interp_h3_vol = interp2d(vol_value3_vol,shap_value3_vol,histogram3_vol)
        interp_h4_vol = interp2d(vol_value4_vol,shap_value4_vol,histogram4_vol)
        vec_vol_vol = np.linspace(min_vol_vol,max_vol_vol,1000)
        vec_shap_vol = np.linspace(min_shap_vol,max_shap_vol,1000)
        vol_grid_vol,shap_grid_vol = np.meshgrid(vec_vol_vol,vec_shap_vol)
        histogram_Q1_vol = interp_h1_vol(vec_vol_vol,vec_shap_vol)
        histogram_Q2_vol = interp_h2_vol(vec_vol_vol,vec_shap_vol)
        histogram_Q3_vol = interp_h3_vol(vec_vol_vol,vec_shap_vol)
        histogram_Q4_vol = interp_h4_vol(vec_vol_vol,vec_shap_vol)
        histogram_Q1_vol[histogram_Q1_vol<3] = 0
        histogram_Q2_vol[histogram_Q2_vol<3] = 0
        histogram_Q3_vol[histogram_Q3_vol<3] = 0
        histogram_Q4_vol[histogram_Q4_vol<3] = 0
        histogram_Q1_vol /= np.max(histogram_Q1_vol)
        histogram_Q2_vol /= np.max(histogram_Q2_vol)
        histogram_Q3_vol /= np.max(histogram_Q3_vol)
        histogram_Q4_vol /= np.max(histogram_Q4_vol)
        fs = 20
        xmin = 0
        xmax = 3
        ymin = 0
        ymax = 40
        fig=plt.figure()
        ax = plt.axes()
        plt.pcolor(vol_grid_vol,shap_grid_vol,histogram_Q1_vol.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$S^+\cdot10^6$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_vol_SHAPvol_'+colormap+'_30+_Q1.png')
        fig=plt.figure()
        ax = plt.axes()
        plt.pcolor(vol_grid_vol,shap_grid_vol,histogram_Q2_vol.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$S^+\cdot10^6$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_vol_SHAPvol_'+colormap+'_30+_Q2.png')
        fig=plt.figure()
        ax = plt.axes()
        plt.pcolor(vol_grid_vol,shap_grid_vol,histogram_Q3_vol.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$S^+\cdot10^6$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_vol_SHAPvol_'+colormap+'_30+_Q3.png')
        fig=plt.figure()
        ax = plt.axes()
        plt.pcolor(vol_grid_vol,shap_grid_vol,histogram_Q4_vol.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$S^+\cdot10^6$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_vol_SHAPvol_'+colormap+'_30+_Q4.png')
        
        
        
    def plot_shaps_uv(self,colormap='viridis'):
        """ 
        Function for plotting the results of the SHAP vs the Reynolds stress
        """
        import matplotlib.pyplot as plt
        import matplotlib as mpl
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/')
        except:
            pass
        volume_size_wa = 50 #1e3*(np.array(volume_wa)-volfilt)/(voltot-volfilt)+50
        volume_size_wd = 50 #1e3*(np.array(volume_wd)-volfilt)/(voltot-volfilt)+50
        fs = 20
        fig = plt.figure()
        ax = plt.axes()
        if self.wallattach:
            plt.scatter(self.uv_uvtot_wa,self.shap_wa,c=self.event_wa,marker='o',\
                        linewidths=0.5,edgecolors='black',s=volume_size_wa,\
                        cmap=plt.cm.get_cmap(colormap,4),vmin=1,vmax=4)
        plt.scatter(self.uv_uvtot_wd,self.shap_wd,c=self.event_wd,marker='s',\
                    linewidths=0.5,edgecolors='black',s=volume_size_wd,\
                    cmap=plt.cm.get_cmap(colormap,4),vmin=1,vmax=4)
        plt.grid()
        plt.xlabel('$\overline{uv}_e/\overline{uv}_\mathrm{tot}$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        handles = [mpl.lines.Line2D([0],[0],marker='o',markerfacecolor='w',\
                                    markeredgecolor='k',markersize=1, ls=''),\
                   mpl.lines.Line2D([0],[0],marker='s',markerfacecolor='w',\
                                    markeredgecolor='k',markersize=1, ls='')]
        labels= ['W-A','W-D']
        if self.wallattach:
            plt.legend(handles,labels,fontsize=fs,markerscale=10) 
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(ticks=[1,2,3,4],cax = cbaxes)
        cb.ax.set_yticklabels(['Outward\ninteraction','Ejection',\
                               'Inward\ninteraction','Sweep'],fontsize=fs-4)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/uv_SHAP_'+colormap+'_30+.png')
        fig = plt.figure()
        ax = plt.axes()
        cmap_fill = plt.cm.get_cmap('viridis', 10)
        x0 = 0
        x0b = 5
        x1 = 1
        x2 = 16
        x3 = 30
        y0_1 = 12
        y1_1 = 24
        y0_2 = 0
        y1_2 = 0
        ytop = 40
        ytop2 = y1_1
#        x0 = 0
#        x0b = 20
#        x1 = 2
#        x2 = 24
#        x3 = 35
#        y0_1 = 15
#        y1_1 = 25
#        y0_2 = 0
#        y1_2 = 2
#        ytop = 35
        plt.fill_between([x0,x1,x0b,x2],[y0_1,y1_1,y1_1,y1_1],[y0_2,y0_2,y0_2,y1_2],\
                         color=cmap_fill(0.9),alpha=0.3)
        plt.fill_between([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,ytop,ytop],\
                         [y1_1,y1_1,y1_1],color=cmap_fill(0.5),alpha=0.3)
        plt.fill_between([x2,x3],[y1_2,y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2)],[ytop2,ytop2],\
                         color=cmap_fill(0.1),alpha=0.3)
        if self.wallattach:
            plt.scatter(self.uv_uvtot_wa_vol,self.shap_wa_vol,c=self.event_wa,marker='o',\
                        linewidths=0.5,edgecolors='black',s=volume_size_wa,\
                        cmap=plt.cm.get_cmap(colormap,4),vmin=1,vmax=4)
        plt.scatter(self.uv_uvtot_wd_vol,self.shap_wd_vol,c=self.event_wd,marker='s',\
                    linewidths=0.5,edgecolors='black',s=volume_size_wd,\
                    cmap=plt.cm.get_cmap(colormap,4),vmin=1,vmax=4)
        plt.plot([x0,x0],[y0_1,y0_2],color='k')
        plt.plot([x0,x1,x0b,x2],[y0_1,y1_1,y1_1,y1_1],color='k')
        plt.plot([x0,x1,x0b,x2],[y0_2,y0_2,y0_2,y1_2],color='k')
        plt.plot([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,ytop,ytop],color='k')
        plt.plot([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,y1_1,y1_1],color='k')
        plt.plot([x2,x3],[y1_2,y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2)],color='k')
        plt.plot([x3,x3],[y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2),ytop2],color='k')
        plt.plot([x2,x3],[ytop2,ytop2],color='k')
        plt.plot([x2,x2],[y1_2,y1_1],color='k')
        plt.plot([x2,x2],[ytop,y1_1],color='k')
        plt.text(5, 10, 'A', fontsize = 20)
        plt.text(20, 10, 'B', fontsize = 20)   
        plt.text(4, 22, 'C', fontsize = 20) 
#        plt.text(20, 10, 'A', fontsize = 20)
#        plt.text(30, 10, 'B', fontsize = 20)   
#        plt.text(5, 30, 'C', fontsize = 20) 
        plt.grid()
        plt.xlabel('$\overline{uv}_e/(\overline{uv}_\mathrm{tot}S^+)\cdot10^{-7}$',\
                   fontsize=fs)
        plt.ylabel(self.ylabel_shap_vol,fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        handles = [mpl.lines.Line2D([0],[0],marker='o',markerfacecolor='w',\
                                    markeredgecolor='k',markersize=1, ls=''),\
                   mpl.lines.Line2D([0],[0],marker='s',markerfacecolor='w',\
                                    markeredgecolor='k',markersize=1, ls='')]
        labels= ['W-A','W-D']
        if self.wallattach:
            plt.legend(handles,labels,fontsize=fs,markerscale=10) 
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(ticks=[1,2,3,4],cax = cbaxes)
        cb.ax.set_yticklabels(['Outward\ninteraction','Ejection',\
                               'Inward\ninteraction','Sweep'],fontsize=fs-4)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/uvvol_SHAPvol_'+colormap+'_30+.png')
        fig = plt.figure()
        ax = plt.axes()
        if self.wallattach:
            plt.scatter(self.uv_vol_uvtot_vol_wa,self.shap_wa_vol,c=self.event_wa,marker='o',\
                        linewidths=0.5,edgecolors='black',s=volume_size_wa,\
                        cmap=plt.cm.get_cmap(colormap,4),vmin=1,vmax=4)
        plt.scatter(self.uv_vol_uvtot_vol_wd,self.shap_wd_vol,c=self.event_wd,marker='s',\
                    linewidths=0.5,edgecolors='black',s=volume_size_wd,\
                    cmap=plt.cm.get_cmap(colormap,4),vmin=1,vmax=4)
        plt.grid()
        plt.xlabel('$(\overline{uv}_e/S^+)/(\overline{uv}/S^+)_\mathrm{tot}$',\
                   fontsize=fs)
        plt.ylabel(self.ylabel_shap_vol,fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        handles = [mpl.lines.Line2D([0],[0],marker='o',markerfacecolor='w',\
                                    markeredgecolor='k',markersize=1, ls=''),\
                   mpl.lines.Line2D([0],[0],marker='s',markerfacecolor='w',\
                                    markeredgecolor='k',markersize=1, ls='')]
        labels= ['W-A','W-D']
        if self.wallattach:
            plt.legend(handles,labels,fontsize=fs,markerscale=10) 
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(ticks=[1,2,3,4],cax = cbaxes)
        cb.ax.set_yticklabels(['Outward\ninteraction','Ejection',\
                               'Inward\ninteraction','Sweep'],fontsize=fs-4)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/uvvoluvoltot_SHAPvol_'+colormap+'_30+.png')
        
       
        
    def plot_shaps_uv_pdf(self,colormap='viridis',bin_num=50,lev_val=5,alf=0.5):
        """ 
        Function for plotting the results of the SHAP vs the Reynolds stress
        """
        import matplotlib.pyplot as plt
        import matplotlib as mpl    
        from scipy.interpolate import interp2d
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/')
        except:
            pass
        xhistmin = np.min([np.min(self.uv_uvtot_1),np.min(self.uv_uvtot_2),np.min(self.uv_uvtot_3),np.min(self.uv_uvtot_4)])/1.2
        xhistmax = np.max([np.max(self.uv_uvtot_1),np.max(self.uv_uvtot_2),np.max(self.uv_uvtot_3),np.max(self.uv_uvtot_4)])*1.2
        yhistmin = np.min([np.min(self.shap_1),np.min(self.shap_2),np.min(self.shap_3),np.min(self.shap_4)])/1.2
        yhistmax = np.max([np.max(self.shap_1),np.max(self.shap_2),np.max(self.shap_3),np.max(self.shap_4)])*1.2
        histogram1,uv_value1,shap_value1 = np.histogram2d(self.uv_uvtot_1,self.shap_1,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram2,uv_value2,shap_value2 = np.histogram2d(self.uv_uvtot_2,self.shap_2,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram3,uv_value3,shap_value3 = np.histogram2d(self.uv_uvtot_3,self.shap_3,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram4,uv_value4,shap_value4 = np.histogram2d(self.uv_uvtot_4,self.shap_4,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        uv_value1 = uv_value1[:-1]+np.diff(uv_value1)/2
        shap_value1 = shap_value1[:-1]+np.diff(shap_value1)/2
        uv_value2 = uv_value2[:-1]+np.diff(uv_value2)/2
        shap_value2 = shap_value2[:-1]+np.diff(shap_value2)/2
        uv_value3 = uv_value3[:-1]+np.diff(uv_value3)/2
        shap_value3 = shap_value3[:-1]+np.diff(shap_value3)/2
        uv_value4 = uv_value4[:-1]+np.diff(uv_value4)/2
        shap_value4 = shap_value4[:-1]+np.diff(shap_value4)/2
        min_uv = np.min([uv_value1,uv_value2,uv_value3,uv_value4])
        max_uv = np.max([uv_value1,uv_value2,uv_value3,uv_value4])
        min_shap = np.min([shap_value1,shap_value2,shap_value3,shap_value4])
        max_shap = np.max([shap_value1,shap_value2,shap_value3,shap_value4])
        interp_h1 = interp2d(uv_value1,shap_value1,histogram1)
        interp_h2 = interp2d(uv_value2,shap_value2,histogram2)
        interp_h3 = interp2d(uv_value3,shap_value3,histogram3)
        interp_h4 = interp2d(uv_value4,shap_value4,histogram4)
        vec_uv = np.linspace(min_uv,max_uv,1000)
        vec_shap = np.linspace(min_shap,max_shap,1000)
        uv_grid,shap_grid = np.meshgrid(vec_uv,vec_shap)
        histogram_Q1 = interp_h1(vec_uv,vec_shap)
        histogram_Q2 = interp_h2(vec_uv,vec_shap)
        histogram_Q3 = interp_h3(vec_uv,vec_shap)
        histogram_Q4 = interp_h4(vec_uv,vec_shap)
        fs = 20
        plt.figure()
        color11 = plt.cm.get_cmap(colormap,4).colors[0,0]
        color12 = plt.cm.get_cmap(colormap,4).colors[0,1]
        color13 = plt.cm.get_cmap(colormap,4).colors[0,2]
        color21 = plt.cm.get_cmap(colormap,4).colors[1,0]
        color22 = plt.cm.get_cmap(colormap,4).colors[1,1]
        color23 = plt.cm.get_cmap(colormap,4).colors[1,2]
        color31 = plt.cm.get_cmap(colormap,4).colors[2,0]
        color32 = plt.cm.get_cmap(colormap,4).colors[2,1]
        color33 = plt.cm.get_cmap(colormap,4).colors[2,2]
        color41 = plt.cm.get_cmap(colormap,4).colors[3,0]
        color42 = plt.cm.get_cmap(colormap,4).colors[3,1]
        color43 = plt.cm.get_cmap(colormap,4).colors[3,2]
        plt.contourf(uv_grid,shap_grid,histogram_Q1.T,levels=[lev_val,1e5*lev_val],colors=[(color11,color12,color13)],alpha=alf)
        plt.contourf(uv_grid,shap_grid,histogram_Q2.T,levels=[lev_val,1e5*lev_val],colors=[(color21,color22,color23)],alpha=alf)
        plt.contourf(uv_grid,shap_grid,histogram_Q3.T,levels=[lev_val,1e5*lev_val],colors=[(color31,color32,color33)],alpha=alf)
        plt.contourf(uv_grid,shap_grid,histogram_Q4.T,levels=[lev_val,1e5*lev_val],colors=[(color41,color42,color43)],alpha=alf)
        plt.contour(uv_grid,shap_grid,histogram_Q1.T,levels=[lev_val],colors=[(color11,color12,color13)])
        plt.contour(uv_grid,shap_grid,histogram_Q2.T,levels=[lev_val],colors=[(color21,color22,color23)])
        plt.contour(uv_grid,shap_grid,histogram_Q3.T,levels=[lev_val],colors=[(color31,color32,color33)])
        plt.contour(uv_grid,shap_grid,histogram_Q4.T,levels=[lev_val],colors=[(color41,color42,color43)])
        plt.xlim([0,1])
        plt.ylim([0,30])
        plt.grid()
        plt.xlabel('$\overline{uv}_e/(\overline{uv}_\mathrm{tot})$',\
                   fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        handles = [mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color11,color12,color13,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color11,color12,color13,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color21,color22,color23,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color21,color22,color23,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color31,color32,color33,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color31,color32,color33,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color41,color42,color43,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color41,color42,color43,alf))]
        labels= ['Outward\ninteractions','Ejections','Inward\ninteractions','Sweeps']
        plt.legend(handles,labels,fontsize=fs-4,loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_uvuvtot_SHAP_'+colormap+'_30+.png')
        xhistmin = np.min([np.min(self.uv_uvtot_1_vol),np.min(self.uv_uvtot_2_vol),np.min(self.uv_uvtot_3_vol),np.min(self.uv_uvtot_4_vol)])/1.2
        xhistmax = np.max([np.max(self.uv_uvtot_1_vol),np.max(self.uv_uvtot_2_vol),np.max(self.uv_uvtot_3_vol),np.max(self.uv_uvtot_4_vol)])*1.2
        yhistmin = np.min([np.min(self.shap_1_vol),np.min(self.shap_2_vol),np.min(self.shap_3_vol),np.min(self.shap_4_vol)])/1.2
        yhistmax = np.max([np.max(self.shap_1_vol),np.max(self.shap_2_vol),np.max(self.shap_3_vol),np.max(self.shap_4_vol)])*1.2
        histogram1_vol,uv_value1_vol,shap_value1_vol = np.histogram2d(self.uv_uvtot_1_vol,self.shap_1_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram2_vol,uv_value2_vol,shap_value2_vol = np.histogram2d(self.uv_uvtot_2_vol,self.shap_2_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram3_vol,uv_value3_vol,shap_value3_vol = np.histogram2d(self.uv_uvtot_3_vol,self.shap_3_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram4_vol,uv_value4_vol,shap_value4_vol = np.histogram2d(self.uv_uvtot_4_vol,self.shap_4_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        uv_value1_vol = uv_value1_vol[:-1]+np.diff(uv_value1_vol)/2
        shap_value1_vol = shap_value1_vol[:-1]+np.diff(shap_value1_vol)/2
        uv_value2_vol = uv_value2_vol[:-1]+np.diff(uv_value2_vol)/2
        shap_value2_vol = shap_value2_vol[:-1]+np.diff(shap_value2_vol)/2
        uv_value3_vol = uv_value3_vol[:-1]+np.diff(uv_value3_vol)/2
        shap_value3_vol = shap_value3_vol[:-1]+np.diff(shap_value3_vol)/2
        uv_value4_vol = uv_value4_vol[:-1]+np.diff(uv_value4_vol)/2
        shap_value4_vol = shap_value4_vol[:-1]+np.diff(shap_value4_vol)/2
        min_uv_vol = np.min([uv_value1_vol,uv_value2_vol,uv_value3_vol,uv_value4_vol])
        max_uv_vol = np.max([uv_value1_vol,uv_value2_vol,uv_value3_vol,uv_value4_vol])
        min_shap_vol = np.min([shap_value1_vol,shap_value2_vol,shap_value3_vol,shap_value4_vol])
        max_shap_vol = np.max([shap_value1_vol,shap_value2_vol,shap_value3_vol,shap_value4_vol])
        interp_h1_vol = interp2d(uv_value1_vol,shap_value1_vol,histogram1_vol)
        interp_h2_vol = interp2d(uv_value2_vol,shap_value2_vol,histogram2_vol)
        interp_h3_vol = interp2d(uv_value3_vol,shap_value3_vol,histogram3_vol)
        interp_h4_vol = interp2d(uv_value4_vol,shap_value4_vol,histogram4_vol)
        vec_uv_vol = np.linspace(min_uv_vol,max_uv_vol,1000)
        vec_shap_vol = np.linspace(min_shap_vol,max_shap_vol,1000)
        uv_grid_vol,shap_grid_vol = np.meshgrid(vec_uv_vol,vec_shap_vol)
        histogram_Q1_vol = interp_h1_vol(vec_uv_vol,vec_shap_vol)
        histogram_Q2_vol = interp_h2_vol(vec_uv_vol,vec_shap_vol)
        histogram_Q3_vol = interp_h3_vol(vec_uv_vol,vec_shap_vol)
        histogram_Q4_vol = interp_h4_vol(vec_uv_vol,vec_shap_vol)
        fs = 20
        plt.figure()
        cmap_fill = plt.cm.get_cmap('viridis', 10)
        x0 = 0
        x0b = 5
        x1 = 1
        x2 = 16
        x3 = 30
        y0_1 = 12
        y1_1 = 24
        y0_2 = 0
        y1_2 = 0
        ytop = 40
        ytop2 = y1_1
        plt.fill_between([x0,x1,x0b,x2],[y0_1,y1_1,y1_1,y1_1],[y0_2,y0_2,y0_2,y1_2],\
                         color=cmap_fill(0.9),alpha=0.1)
        plt.fill_between([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,ytop,ytop],\
                         [y1_1,y1_1,y1_1],color=cmap_fill(0.5),alpha=0.1)
        plt.fill_between([x2,x3],[y1_2,y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2)],[ytop2,ytop2],\
                         color=cmap_fill(0.1),alpha=0.1)
        plt.plot([x0,x0],[y0_1,y0_2],color='k')
        plt.plot([x0,x1,x0b,x2],[y0_1,y1_1,y1_1,y1_1],color='k')
        plt.plot([x0,x1,x0b,x2],[y0_2,y0_2,y0_2,y1_2],color='k')
        plt.plot([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,ytop,ytop],color='k')
        plt.plot([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,y1_1,y1_1],color='k')
        plt.plot([x2,x3],[y1_2,y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2)],color='k')
        plt.plot([x2,x3],[ytop2,ytop2],color='k')
        plt.plot([x2,x2],[y1_2,y1_1],color='k')
        plt.plot([x2,x2],[ytop,y1_1],color='k')
        plt.plot([x3,x3],[y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2),ytop2],color='k')
        plt.text(5, 10, 'A', fontsize = 20)
        plt.text(20, 10, 'B', fontsize = 20)   
        plt.text(4, 26, 'C', fontsize = 20) 
        color11 = plt.cm.get_cmap(colormap,4).colors[0,0]
        color12 = plt.cm.get_cmap(colormap,4).colors[0,1]
        color13 = plt.cm.get_cmap(colormap,4).colors[0,2]
        color21 = plt.cm.get_cmap(colormap,4).colors[1,0]
        color22 = plt.cm.get_cmap(colormap,4).colors[1,1]
        color23 = plt.cm.get_cmap(colormap,4).colors[1,2]
        color31 = plt.cm.get_cmap(colormap,4).colors[2,0]
        color32 = plt.cm.get_cmap(colormap,4).colors[2,1]
        color33 = plt.cm.get_cmap(colormap,4).colors[2,2]
        color41 = plt.cm.get_cmap(colormap,4).colors[3,0]
        color42 = plt.cm.get_cmap(colormap,4).colors[3,1]
        color43 = plt.cm.get_cmap(colormap,4).colors[3,2]
        plt.contourf(uv_grid_vol,shap_grid_vol,histogram_Q1_vol.T,levels=[lev_val,1e5*lev_val],colors=[(color11,color12,color13)],alpha=alf)
        plt.contourf(uv_grid_vol,shap_grid_vol,histogram_Q2_vol.T,levels=[lev_val,1e5*lev_val],colors=[(color21,color22,color23)],alpha=alf)
        plt.contourf(uv_grid_vol,shap_grid_vol,histogram_Q3_vol.T,levels=[lev_val,1e5*lev_val],colors=[(color31,color32,color33)],alpha=alf)
        plt.contourf(uv_grid_vol,shap_grid_vol,histogram_Q4_vol.T,levels=[lev_val,1e5*lev_val],colors=[(color41,color42,color43)],alpha=alf)
        plt.contour(uv_grid_vol,shap_grid_vol,histogram_Q1_vol.T,levels=[lev_val],colors=[(color11,color12,color13)])
        plt.contour(uv_grid_vol,shap_grid_vol,histogram_Q2_vol.T,levels=[lev_val],colors=[(color21,color22,color23)])
        plt.contour(uv_grid_vol,shap_grid_vol,histogram_Q3_vol.T,levels=[lev_val],colors=[(color31,color32,color33)])
        plt.contour(uv_grid_vol,shap_grid_vol,histogram_Q4_vol.T,levels=[lev_val],colors=[(color41,color42,color43)])
        plt.xlim([0,25])
        plt.ylim([0,30])
        plt.grid()
        plt.xlabel('$\overline{uv}_e/(\overline{uv}_\mathrm{tot}S^+)\cdot10^{-7}$',\
                   fontsize=fs)
        plt.ylabel(self.ylabel_shap_vol,fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        handles = [mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color11,color12,color13,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color11,color12,color13,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color21,color22,color23,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color21,color22,color23,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color31,color32,color33,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color31,color32,color33,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color41,color42,color43,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color41,color42,color43,alf))]
        labels= ['Outward\ninteractions','Ejections','Inward\ninteractions','Sweeps']
        plt.legend(handles,labels,fontsize=fs-4,loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_uvuvtotvol_SHAPvol_'+colormap+'_30+.png')
        
                    
    def plot_shaps_uv_pdf_probability(self,colormap='viridis',bin_num=100,lev_val=2.5,alf=0.5):
        """ 
        Function for plotting the results of the SHAP vs the Reynolds stress
        """
        import matplotlib.pyplot as plt
        import matplotlib as mpl    
        from scipy.interpolate import interp2d
        import matplotlib.colors as colors
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/')
        except:
            pass
        xhistmin = np.min([np.min(self.uv_uvtot_1),np.min(self.uv_uvtot_2),np.min(self.uv_uvtot_3),np.min(self.uv_uvtot_4)])/1.2
        xhistmax = np.max([np.max(self.uv_uvtot_1),np.max(self.uv_uvtot_2),np.max(self.uv_uvtot_3),np.max(self.uv_uvtot_4)])*1.2
        yhistmin = np.min([np.min(self.shap_1),np.min(self.shap_2),np.min(self.shap_3),np.min(self.shap_4)])/1.2
        yhistmax = np.max([np.max(self.shap_1),np.max(self.shap_2),np.max(self.shap_3),np.max(self.shap_4)])*1.2
        histogram1,uv_value1,shap_value1 = np.histogram2d(self.uv_uvtot_1,self.shap_1,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram2,uv_value2,shap_value2 = np.histogram2d(self.uv_uvtot_2,self.shap_2,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram3,uv_value3,shap_value3 = np.histogram2d(self.uv_uvtot_3,self.shap_3,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram4,uv_value4,shap_value4 = np.histogram2d(self.uv_uvtot_4,self.shap_4,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        uv_value1 = uv_value1[:-1]+np.diff(uv_value1)/2
        shap_value1 = shap_value1[:-1]+np.diff(shap_value1)/2
        uv_value2 = uv_value2[:-1]+np.diff(uv_value2)/2
        shap_value2 = shap_value2[:-1]+np.diff(shap_value2)/2
        uv_value3 = uv_value3[:-1]+np.diff(uv_value3)/2
        shap_value3 = shap_value3[:-1]+np.diff(shap_value3)/2
        uv_value4 = uv_value4[:-1]+np.diff(uv_value4)/2
        shap_value4 = shap_value4[:-1]+np.diff(shap_value4)/2
        min_uv = np.min([uv_value1,uv_value2,uv_value3,uv_value4])
        max_uv = np.max([uv_value1,uv_value2,uv_value3,uv_value4])
        min_shap = np.min([shap_value1,shap_value2,shap_value3,shap_value4])
        max_shap = np.max([shap_value1,shap_value2,shap_value3,shap_value4])
        interp_h1 = interp2d(uv_value1,shap_value1,histogram1)
        interp_h2 = interp2d(uv_value2,shap_value2,histogram2)
        interp_h3 = interp2d(uv_value3,shap_value3,histogram3)
        interp_h4 = interp2d(uv_value4,shap_value4,histogram4)
        vec_uv = np.linspace(min_uv,max_uv,1000)
        vec_shap = np.linspace(min_shap,max_shap,1000)
        uv_grid,shap_grid = np.meshgrid(vec_uv,vec_shap)
        histogram_Q1 = interp_h1(vec_uv,vec_shap)
        histogram_Q2 = interp_h2(vec_uv,vec_shap)
        histogram_Q3 = interp_h3(vec_uv,vec_shap)
        histogram_Q4 = interp_h4(vec_uv,vec_shap)
        histogram_Q1[histogram_Q1<5] = 0
        histogram_Q2[histogram_Q2<5] = 0
        histogram_Q3[histogram_Q3<5] = 0
        histogram_Q4[histogram_Q4<5] = 0
        histogram_Q1 /= np.max(histogram_Q1)
        histogram_Q2 /= np.max(histogram_Q2)
        histogram_Q3 /= np.max(histogram_Q3)
        histogram_Q4 /= np.max(histogram_Q4)
        fs = 20
        xmin = 0
        xmax = 1
        ymin = 0
        ymax = 30      
        fig=plt.figure()
        ax = plt.axes()
        plt.pcolor(uv_grid,shap_grid,histogram_Q1.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$\overline{uv}_e/\overline{uv}_\mathrm{tot}$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_uvuvtot_SHAP_'+colormap+'_30+_Q1.png')
        fig=plt.figure()
        ax = plt.axes()
        plt.pcolor(uv_grid,shap_grid,histogram_Q2.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$\overline{uv}_e/\overline{uv}_\mathrm{tot}$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_uvuvtot_SHAP_'+colormap+'_30+_Q2.png')
        fig=plt.figure()
        ax = plt.axes()
        plt.pcolor(uv_grid,shap_grid,histogram_Q3.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$\overline{uv}_e/\overline{uv}_\mathrm{tot}$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_uvuvtot_SHAP_'+colormap+'_30+_Q3.png')
        fig=plt.figure()
        ax = plt.axes()
        plt.pcolor(uv_grid,shap_grid,histogram_Q4.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$\overline{uv}_e/\overline{uv}_\mathrm{tot}$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_uvuvtot_SHAP_'+colormap+'_30+_Q4.png')
        
        xhistmin = np.min([np.min(self.uv_uvtot_1_vol),np.min(self.uv_uvtot_2_vol),np.min(self.uv_uvtot_3_vol),np.min(self.uv_uvtot_4_vol)])/1.2
        xhistmax = np.max([np.max(self.uv_uvtot_1_vol),np.max(self.uv_uvtot_2_vol),np.max(self.uv_uvtot_3_vol),np.max(self.uv_uvtot_4_vol)])*1.2
        yhistmin = np.min([np.min(self.shap_1_vol),np.min(self.shap_2_vol),np.min(self.shap_3_vol),np.min(self.shap_4_vol)])/1.2
        yhistmax = np.max([np.max(self.shap_1_vol),np.max(self.shap_2_vol),np.max(self.shap_3_vol),np.max(self.shap_4_vol)])*1.2
        histogram1_vol,uv_value1_vol,shap_value1_vol = np.histogram2d(self.uv_uvtot_1_vol,self.shap_1_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram2_vol,uv_value2_vol,shap_value2_vol = np.histogram2d(self.uv_uvtot_2_vol,self.shap_2_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram3_vol,uv_value3_vol,shap_value3_vol = np.histogram2d(self.uv_uvtot_3_vol,self.shap_3_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram4_vol,uv_value4_vol,shap_value4_vol = np.histogram2d(self.uv_uvtot_4_vol,self.shap_4_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        uv_value1_vol = uv_value1_vol[:-1]+np.diff(uv_value1_vol)/2
        shap_value1_vol = shap_value1_vol[:-1]+np.diff(shap_value1_vol)/2
        uv_value2_vol = uv_value2_vol[:-1]+np.diff(uv_value2_vol)/2
        shap_value2_vol = shap_value2_vol[:-1]+np.diff(shap_value2_vol)/2
        uv_value3_vol = uv_value3_vol[:-1]+np.diff(uv_value3_vol)/2
        shap_value3_vol = shap_value3_vol[:-1]+np.diff(shap_value3_vol)/2
        uv_value4_vol = uv_value4_vol[:-1]+np.diff(uv_value4_vol)/2
        shap_value4_vol = shap_value4_vol[:-1]+np.diff(shap_value4_vol)/2
        min_uv_vol = np.min([uv_value1_vol,uv_value2_vol,uv_value3_vol,uv_value4_vol])
        max_uv_vol = np.max([uv_value1_vol,uv_value2_vol,uv_value3_vol,uv_value4_vol])
        min_shap_vol = np.min([shap_value1_vol,shap_value2_vol,shap_value3_vol,shap_value4_vol])
        max_shap_vol = np.max([shap_value1_vol,shap_value2_vol,shap_value3_vol,shap_value4_vol])
        interp_h1_vol = interp2d(uv_value1_vol,shap_value1_vol,histogram1_vol)
        interp_h2_vol = interp2d(uv_value2_vol,shap_value2_vol,histogram2_vol)
        interp_h3_vol = interp2d(uv_value3_vol,shap_value3_vol,histogram3_vol)
        interp_h4_vol = interp2d(uv_value4_vol,shap_value4_vol,histogram4_vol)
        vec_uv_vol = np.linspace(min_uv_vol,max_uv_vol,1000)
        vec_shap_vol = np.linspace(min_shap_vol,max_shap_vol,1000)
        uv_grid_vol,shap_grid_vol = np.meshgrid(vec_uv_vol,vec_shap_vol)
        histogram_Q1_vol = interp_h1_vol(vec_uv_vol,vec_shap_vol)
        histogram_Q2_vol = interp_h2_vol(vec_uv_vol,vec_shap_vol)
        histogram_Q3_vol = interp_h3_vol(vec_uv_vol,vec_shap_vol)
        histogram_Q4_vol = interp_h4_vol(vec_uv_vol,vec_shap_vol)
        histogram_Q1_vol[histogram_Q1_vol<5] = 0
        histogram_Q2_vol[histogram_Q2_vol<5] = 0
        histogram_Q3_vol[histogram_Q3_vol<5] = 0
        histogram_Q4_vol[histogram_Q4_vol<5] = 0
        histogram_Q1_vol /= np.max(histogram_Q1_vol)
        histogram_Q2_vol /= np.max(histogram_Q2_vol)
        histogram_Q3_vol /= np.max(histogram_Q3_vol)
        histogram_Q4_vol /= np.max(histogram_Q4_vol)
        cmap_fill = plt.cm.get_cmap('viridis', 10)
        x0 = 0
        x0b = 5
        x1 = 1
        x2 = 16
        x3 = 30
        y0_1 = 12
        y1_1 = 24
        y0_2 = 0
        y1_2 = 0
        ytop = 40
        ytop2 = y1_1
        fs = 20    
        xmin = 0
        xmax = 25
        ymin = 0
        ymax = 30    
        fig=plt.figure()
        ax = plt.axes()
        plt.fill_between([x0,x1,x0b,x2],[y0_1,y1_1,y1_1,y1_1],[y0_2,y0_2,y0_2,y1_2],\
                         color=cmap_fill(0.9),alpha=0.1)
        plt.fill_between([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,ytop,ytop],\
                         [y1_1,y1_1,y1_1],color=cmap_fill(0.5),alpha=0.1)
        plt.fill_between([x2,x3],[y1_2,y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2)],[ytop2,ytop2],\
                         color=cmap_fill(0.1),alpha=0.1)
        plt.plot([x0,x0],[y0_1,y0_2],color='k')
        plt.plot([x0,x1,x0b,x2],[y0_1,y1_1,y1_1,y1_1],color='k')
        plt.plot([x0,x1,x0b,x2],[y0_2,y0_2,y0_2,y1_2],color='k')
        plt.plot([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,ytop,ytop],color='k')
        plt.plot([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,y1_1,y1_1],color='k')
        plt.plot([x2,x3],[y1_2,y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2)],color='k')
        plt.plot([x2,x3],[ytop2,ytop2],color='k')
        plt.plot([x2,x2],[y1_2,y1_1],color='k')
        plt.plot([x2,x2],[ytop,y1_1],color='k')
        plt.plot([x3,x3],[y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2),ytop2],color='k')
        plt.text(5, 10, 'A', fontsize = 20)
        plt.text(20, 10, 'B', fontsize = 20)   
        plt.text(4, 26, 'C', fontsize = 20) 
        plt.pcolor(uv_grid_vol,shap_grid_vol,histogram_Q1_vol.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$\overline{uv}_e/(\overline{uv}_\mathrm{tot}S^+)\cdot10^{-7}$',\
                   fontsize=fs)
        plt.ylabel(self.ylabel_shap_vol,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_uvuvtotvol_SHAPvol_'+colormap+'_30+_Q1.png')
        fig=plt.figure()
        ax = plt.axes()
        plt.fill_between([x0,x1,x0b,x2],[y0_1,y1_1,y1_1,y1_1],[y0_2,y0_2,y0_2,y1_2],\
                         color=cmap_fill(0.9),alpha=0.1)
        plt.fill_between([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,ytop,ytop],\
                         [y1_1,y1_1,y1_1],color=cmap_fill(0.5),alpha=0.1)
        plt.fill_between([x2,x3],[y1_2,y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2)],[ytop2,ytop2],\
                         color=cmap_fill(0.1),alpha=0.1)
        plt.plot([x0,x0],[y0_1,y0_2],color='k')
        plt.plot([x0,x1,x0b,x2],[y0_1,y1_1,y1_1,y1_1],color='k')
        plt.plot([x0,x1,x0b,x2],[y0_2,y0_2,y0_2,y1_2],color='k')
        plt.plot([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,ytop,ytop],color='k')
        plt.plot([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,y1_1,y1_1],color='k')
        plt.plot([x2,x3],[y1_2,y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2)],color='k')
        plt.plot([x2,x3],[ytop2,ytop2],color='k')
        plt.plot([x2,x2],[y1_2,y1_1],color='k')
        plt.plot([x2,x2],[ytop,y1_1],color='k')
        plt.plot([x3,x3],[y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2),ytop2],color='k') 
        plt.text(5, 10, 'A', fontsize = 20)
        plt.text(20, 10, 'B', fontsize = 20)   
        plt.text(4, 26, 'C', fontsize = 20) 
        plt.pcolor(uv_grid_vol,shap_grid_vol,histogram_Q2_vol.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$\overline{uv}_e/(\overline{uv}_\mathrm{tot}S^+)\cdot10^{-7}$',\
                   fontsize=fs)
        plt.ylabel(self.ylabel_shap_vol,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_uvuvtotvol_SHAPvol_'+colormap+'_30+_Q2.png')
        fig=plt.figure()
        ax = plt.axes()
        plt.fill_between([x0,x1,x0b,x2],[y0_1,y1_1,y1_1,y1_1],[y0_2,y0_2,y0_2,y1_2],\
                         color=cmap_fill(0.9),alpha=0.1)
        plt.fill_between([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,ytop,ytop],\
                         [y1_1,y1_1,y1_1],color=cmap_fill(0.5),alpha=0.1)
        plt.fill_between([x2,x3],[y1_2,y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2)],[ytop2,ytop2],\
                         color=cmap_fill(0.1),alpha=0.1)
        plt.plot([x0,x0],[y0_1,y0_2],color='k')
        plt.plot([x0,x1,x0b,x2],[y0_1,y1_1,y1_1,y1_1],color='k')
        plt.plot([x0,x1,x0b,x2],[y0_2,y0_2,y0_2,y1_2],color='k')
        plt.plot([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,ytop,ytop],color='k')
        plt.plot([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,y1_1,y1_1],color='k')
        plt.plot([x2,x3],[y1_2,y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2)],color='k')
        plt.plot([x2,x3],[ytop2,ytop2],color='k')
        plt.plot([x2,x2],[y1_2,y1_1],color='k')
        plt.plot([x2,x2],[ytop,y1_1],color='k')
        plt.plot([x3,x3],[y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2),ytop2],color='k')
        plt.text(5, 10, 'A', fontsize = 20)
        plt.text(20, 10, 'B', fontsize = 20)   
        plt.text(4, 26, 'C', fontsize = 20) 
        plt.pcolor(uv_grid_vol,shap_grid_vol,histogram_Q3_vol.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$\overline{uv}_e/(\overline{uv}_\mathrm{tot}S^+)\cdot10^{-7}$',\
                   fontsize=fs)
        plt.ylabel(self.ylabel_shap_vol,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_uvuvtotvol_SHAPvol_'+colormap+'_30+_Q3.png')
        fig=plt.figure()
        ax = plt.axes()
        plt.fill_between([x0,x1,x0b,x2],[y0_1,y1_1,y1_1,y1_1],[y0_2,y0_2,y0_2,y1_2],\
                         color=cmap_fill(0.9),alpha=0.1)
        plt.fill_between([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,ytop,ytop],\
                         [y1_1,y1_1,y1_1],color=cmap_fill(0.5),alpha=0.1)
        plt.fill_between([x2,x3],[y1_2,y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2)],[ytop2,ytop2],\
                         color=cmap_fill(0.1),alpha=0.1)
        plt.plot([x0,x0],[y0_1,y0_2],color='k')
        plt.plot([x0,x1,x0b,x2],[y0_1,y1_1,y1_1,y1_1],color='k')
        plt.plot([x0,x1,x0b,x2],[y0_2,y0_2,y0_2,y1_2],color='k')
        plt.plot([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,ytop,ytop],color='k')
        plt.plot([x1,(ytop-y1_1)*(x1-x0)/(y1_1-y0_1)+x1,x2],[y1_1,y1_1,y1_1],color='k')
        plt.plot([x2,x3],[y1_2,y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2)],color='k')
        plt.plot([x2,x3],[ytop2,ytop2],color='k')
        plt.plot([x2,x2],[y1_2,y1_1],color='k')
        plt.plot([x2,x2],[ytop,y1_1],color='k')
        plt.plot([x3,x3],[y1_2+(y1_2-y0_2)/(x2-x0b)*(x3-x2),ytop2],color='k')
        plt.text(5, 10, 'A', fontsize = 20)
        plt.text(20, 10, 'B', fontsize = 20)   
        plt.text(4, 26, 'C', fontsize = 20) 
        plt.pcolor(uv_grid_vol,shap_grid_vol,histogram_Q4_vol.T,cmap=colormap,\
                   norm=colors.LogNorm(vmin=1e-3,vmax=1))
        plt.grid()
        plt.xlim([xmin,xmax])
        plt.ylim([ymin,ymax])
        plt.xlabel('$\overline{uv}_e/(\overline{uv}_\mathrm{tot}S^+)\cdot10^{-7}$',\
                   fontsize=fs)
        plt.ylabel(self.ylabel_shap_vol,fontsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        plt.tick_params(axis='both',which='major',labelsize=fs)
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(cax = cbaxes)
        cb.ax.set_ylabel('$N/N_{tot}$',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_uvuvtotvol_SHAPvol_'+colormap+'_30+_Q4.png')

    
    
    
    def plot_shaps_kde(self,colormap='viridis',fit_bw=False):
        """ 
        Function for plotting the results of the SHAP vs the Reynolds stress
        """
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/')
        except:
            pass
        kdedata_SHAP_1 = np.array(self.shap_1).reshape(-1,1)
        kdedata_SHAP_2 = np.array(self.shap_2).reshape(-1,1)
        kdedata_SHAP_3 = np.array(self.shap_3).reshape(-1,1)
        kdedata_SHAP_4 = np.array(self.shap_4).reshape(-1,1) 
        kdedata_SHAP_13 = np.concatenate((kdedata_SHAP_1,kdedata_SHAP_3))
        kdedata_SHAPvol_1 = np.array(self.shap_1_vol).reshape(-1,1)
        kdedata_SHAPvol_2 = np.array(self.shap_2_vol).reshape(-1,1)
        kdedata_SHAPvol_3 = np.array(self.shap_3_vol).reshape(-1,1)
        kdedata_SHAPvol_4 = np.array(self.shap_4_vol).reshape(-1,1)
        kdedata_SHAPvol_13 = np.concatenate((kdedata_SHAPvol_1,kdedata_SHAPvol_3))
        from sklearn.neighbors import KernelDensity  
        from sklearn.model_selection import GridSearchCV,LeaveOneOut
        ker = 'gaussian'
        if fit_bw:
            minexp = -5
            maxexp = 2
            nexp = 10
            fac_exp = 1
            bandwidths1 = fac_exp*10**np.linspace(minexp,maxexp,nexp)
            bandwidths2 = fac_exp*10**np.linspace(minexp,maxexp,nexp)
            bandwidths3 = fac_exp*10**np.linspace(minexp,maxexp,nexp)
            bandwidths4 = fac_exp*10**np.linspace(minexp,maxexp,nexp)
            bandwidths13 = fac_exp*10**np.linspace(minexp,maxexp,nexp)
            bandwidths1vol = fac_exp*10**np.linspace(minexp,maxexp,nexp)
            bandwidths2vol = fac_exp*10**np.linspace(minexp,maxexp,nexp)
            bandwidths3vol = fac_exp*10**np.linspace(minexp,maxexp,nexp)
            bandwidths4vol = fac_exp*10**np.linspace(minexp,maxexp,nexp)
            bandwidths13vol = fac_exp*10**np.linspace(minexp,maxexp,nexp)
            kk = 0
            bw1 = 0
            bw2 = 0
            bw3 = 0
            bw4 = 0
            bw13 = 0
            bw1vol = 0
            bw2vol = 0
            bw3vol = 0
            bw4vol = 0
            bw13vol = 0
            while kk<3:
                grid1 = GridSearchCV(KernelDensity(kernel=ker),\
                                     {'bandwidth': bandwidths1},cv=LeaveOneOut())
                grid2 = GridSearchCV(KernelDensity(kernel=ker),\
                                     {'bandwidth': bandwidths2},cv=LeaveOneOut())
                grid3 = GridSearchCV(KernelDensity(kernel=ker),\
                                     {'bandwidth': bandwidths3},cv=LeaveOneOut())
                grid4 = GridSearchCV(KernelDensity(kernel=ker),\
                                     {'bandwidth': bandwidths4},cv=LeaveOneOut())
                grid13 = GridSearchCV(KernelDensity(kernel=ker),\
                                      {'bandwidth': bandwidths13},cv=LeaveOneOut())
                grid1vol = GridSearchCV(KernelDensity(kernel=ker),\
                                        {'bandwidth': bandwidths1vol},\
                                        cv=LeaveOneOut())
                grid2vol = GridSearchCV(KernelDensity(kernel=ker),\
                                        {'bandwidth': bandwidths2vol},\
                                        cv=LeaveOneOut())
                grid3vol = GridSearchCV(KernelDensity(kernel=ker),\
                                        {'bandwidth': bandwidths3vol},\
                                        cv=LeaveOneOut())
                grid4vol = GridSearchCV(KernelDensity(kernel=ker),\
                                        {'bandwidth': bandwidths4vol},\
                                        cv=LeaveOneOut())
                grid13vol = GridSearchCV(KernelDensity(kernel=ker),\
                                         {'bandwidth': bandwidths13vol},\
                                         cv=LeaveOneOut())
                if len(kdedata_SHAP_1) > 0:
                    grid1.fit(kdedata_SHAP_1)
                    bw1 = grid1.best_params_["bandwidth"]
                    grid1vol.fit(kdedata_SHAPvol_1)
                    bw1vol = grid1vol.best_params_["bandwidth"]
                    print('Band width 1: '+str(bw1))
                    print('Band width volume 1: '+str(bw1vol))
                if len(kdedata_SHAP_2) > 0:
                    grid2.fit(kdedata_SHAP_2)
                    bw2 = grid2.best_params_["bandwidth"]
                    grid2vol.fit(kdedata_SHAPvol_2)
                    bw2vol = grid2vol.best_params_["bandwidth"]
                    print('Band width 2: '+str(bw2))
                    print('Band width volume 2: '+str(bw2vol))
                if len(kdedata_SHAP_3) > 0:
                    grid3.fit(kdedata_SHAP_3)
                    bw3 = grid3.best_params_["bandwidth"]
                    grid3vol.fit(kdedata_SHAPvol_3)
                    bw3vol = grid3vol.best_params_["bandwidth"]
                    print('Band width 3: '+str(bw3))
                    print('Band width volume 3: '+str(bw3vol))
                if len(kdedata_SHAP_4) > 0:
                    grid4.fit(kdedata_SHAP_4)
                    bw4 = grid4.best_params_["bandwidth"]
                    grid4vol.fit(kdedata_SHAPvol_4)
                    bw4vol = grid4vol.best_params_["bandwidth"]
                    print('Band width 4: '+str(bw4))
                    print('Band width volume 4: '+str(bw4vol))
                if len(kdedata_SHAP_1) > 0 and len(kdedata_SHAP_3) > 0:
                    grid13.fit(kdedata_SHAP_13)
                    bw13 = grid13.best_params_["bandwidth"]
                    grid13vol.fit(kdedata_SHAPvol_13)
                    bw13vol = grid13vol.best_params_["bandwidth"]
                    print('Band width 13: '+str(bw13))
                    print('Band width volume 13: '+str(bw13vol))
                kk += 1
                incband = (maxexp-minexp)/nexp
                bw1exp = np.log10(bw1/fac_exp)
                bw2exp = np.log10(bw2/fac_exp)
                bw3exp = np.log10(bw3/fac_exp)
                bw4exp = np.log10(bw4/fac_exp)
                bw13exp = np.log10(bw13/fac_exp)
                bw1volexp = np.log10(bw1vol/fac_exp)
                bw2volexp = np.log10(bw2vol/fac_exp)
                bw3volexp = np.log10(bw3vol/fac_exp)
                bw4volexp = np.log10(bw4vol/fac_exp)
                bw13volexp = np.log10(bw13vol/fac_exp)
                bandwidths1 = fac_exp*10**np.linspace(bw1exp-incband,\
                                                      bw1exp+incband,nexp)
                bandwidths2 = fac_exp*10**np.linspace(bw2exp-incband,\
                                                      bw2exp+incband,nexp)
                bandwidths3 = fac_exp*10**np.linspace(bw3exp-incband,\
                                                      bw3exp+incband,nexp)
                bandwidths4 = fac_exp*10**np.linspace(bw4exp-incband,\
                                                      bw4exp+incband,nexp)
                bandwidths13 = fac_exp*10**np.linspace(bw13exp-incband,\
                                                       bw13exp+incband,nexp)
                bandwidths1vol = fac_exp*10**np.linspace(bw1volexp-incband,\
                                                         bw1volexp+incband,nexp)
                bandwidths2vol = fac_exp*10**np.linspace(bw2volexp-incband,\
                                                         bw2volexp+incband,nexp)
                bandwidths3vol = fac_exp*10**np.linspace(bw3volexp-incband,\
                                                         bw3volexp+incband,nexp)
                bandwidths4vol = fac_exp*10**np.linspace(bw4volexp-incband,\
                                                         bw4volexp+incband,nexp)
                bandwidths13vol = fac_exp*10**np.linspace(bw13volexp-incband,\
                                                          bw13volexp+incband,nexp)
        else: #D.W. Scott, “Multivariate Density Estimation: Theory, Practice, and Visualization”, John Wiley & Sons, New York, Chicester, 1992.
            if len(kdedata_SHAP_1) > 0:
                bw1 = np.std(kdedata_SHAP_1)*len(kdedata_SHAP_1)**(-1./(1+4))
                bw1vol = np.std(kdedata_SHAPvol_1)*len(kdedata_SHAPvol_1)**(-1./(1+4))
                print('Band width 1: '+str(bw1))
                print('Band width volume 1: '+str(bw1vol))
            if len(kdedata_SHAP_2) > 0:
                bw2 = np.std(kdedata_SHAP_2)*len(kdedata_SHAP_2)**(-1./(1+4))
                bw2vol = np.std(kdedata_SHAPvol_2)*len(kdedata_SHAPvol_2)**(-1./(1+4))
                print('Band width 2: '+str(bw2))
                print('Band width volume 2: '+str(bw2vol))
            if len(kdedata_SHAP_3) > 0:
                bw3 = np.std(kdedata_SHAP_3)*len(kdedata_SHAP_3)**(-1./(1+4))
                bw3vol = np.std(kdedata_SHAPvol_3)*len(kdedata_SHAPvol_3)**(-1./(1+4))
                print('Band width 3: '+str(bw3))
                print('Band width volume 3: '+str(bw3vol))
            if len(kdedata_SHAP_4) > 0:
                bw4 = np.std(kdedata_SHAP_4)*len(kdedata_SHAP_4)**(-1./(1+4))
                bw4vol = np.std(kdedata_SHAPvol_4)*len(kdedata_SHAPvol_4)**(-1./(1+4))
                print('Band width 4: '+str(bw4))
                print('Band width volume 4: '+str(bw4vol))
            if len(kdedata_SHAP_1) > 0 and len(kdedata_SHAP_3) > 0:
                bw13 = np.std(kdedata_SHAP_13)*len(kdedata_SHAP_13)**(-1./(1+4))
                bw13vol = np.std(kdedata_SHAPvol_13)*len(kdedata_SHAPvol_13)**(-1./(1+4))
                print('Band width 13: '+str(bw13))
                print('Band width volume 13: '+str(bw13vol))
        import matplotlib.pyplot as plt
        import matplotlib as mpl
        plt.figure(20,figsize=(10, 5))
        ax = plt.axes()
        alphval = 0.5
        X_plot = np.linspace(self.shapmin,self.shapmax,self.nbars)[:, np.newaxis]
        try:
            kde1 = KernelDensity(kernel=ker,bandwidth=bw1).fit(kdedata_SHAP_1)
            log_dens1 = kde1.score_samples(X_plot)
            plt.fill_between(X_plot[:, 0],np.exp(log_dens1),y2=0,alpha=alphval,\
                             fc=plt.cm.get_cmap(colormap,4).colors[0,:],\
                             zorder=0,label='Outward\ninteraction') 
            plt.plot(X_plot[:, 0],np.exp(log_dens1),\
                     color=plt.cm.get_cmap(colormap,4).colors[0,:],\
                     zorder=4,linewidth=3) 
        except:
            pass
        try:
            kde2 = KernelDensity(kernel=ker,bandwidth=bw2).fit(kdedata_SHAP_2)
            log_dens2 = kde2.score_samples(X_plot)
            plt.fill_between(X_plot[:, 0],np.exp(log_dens2),y2=0,alpha=alphval,\
                             fc=plt.cm.get_cmap(colormap,4).colors[1,:],\
                             zorder=1,label='Ejection')
            plt.plot(X_plot[:, 0],np.exp(log_dens2),\
                     color=plt.cm.get_cmap(colormap,4).colors[1,:],\
                     zorder=5,linewidth=3)
        except:
            pass
        try:
            kde3 = KernelDensity(kernel=ker,bandwidth=bw3).fit(kdedata_SHAP_3)
            log_dens3 = kde3.score_samples(X_plot)
            plt.fill_between(X_plot[:, 0],np.exp(log_dens3),y2=0,alpha=alphval,\
                             fc=plt.cm.get_cmap(colormap,4).colors[2,:],\
                             zorder=2,label='Inward\ninteraction')
            plt.plot(X_plot[:, 0],np.exp(log_dens3),\
                     color=plt.cm.get_cmap(colormap,4).colors[2,:],\
                     zorder=6,linewidth=3)
        except:
            pass
        try:
            kde4 = KernelDensity(kernel=ker,bandwidth=bw4).fit(kdedata_SHAP_4)
            log_dens4 = kde4.score_samples(X_plot)
            plt.fill_between(X_plot[:, 0],np.exp(log_dens4),y2=0,alpha=alphval,\
                             fc=plt.cm.get_cmap(colormap,4).colors[3,:],\
                             zorder=3,label='Sweep')
            plt.plot(X_plot[:, 0],np.exp(log_dens4),\
                     color=plt.cm.get_cmap(colormap,4).colors[3,:],\
                     zorder=7,linewidth=3)
        except:
            pass
        ax.set_xlabel(self.ylabel_shap,fontsize=20)
        ax.set_ylabel('Normalized Density',fontsize=20)
        plt.tick_params(axis='both', which='major', labelsize=20)   
        ax.set_position([0.15,0.2,0.55,0.65]) 
        ax.tick_params(axis='both', which='major', labelsize=20)
        ax.ticklabel_format(style='sci',scilimits=(0,2))
        ax.xaxis.get_offset_text().set_fontsize(20)
        plt.yscale('log')
        ax.set_ylim([1e-5,1e1])
        plt.legend(fontsize=20, bbox_to_anchor=(1, 1))
        ax.grid() 
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/kde_SHAP_'+colormap+'_30+.png')
        # New figure
        plt.figure(21,figsize=(10, 5))
        ax = plt.axes()
        alphval = 0.5
        X_plot = np.linspace(self.shapminvol,self.shapmaxvol,self.nbars)[:, np.newaxis]
        try:
            kde1 = KernelDensity(kernel=ker,bandwidth=bw1vol).fit(kdedata_SHAPvol_1)
            log_dens1 = kde1.score_samples(X_plot)
            plt.fill_between(X_plot[:, 0],np.exp(log_dens1),y2=0,alpha=alphval,\
                             fc=plt.cm.get_cmap(colormap,4).colors[0,:],\
                             zorder=0,label='Outward\ninteraction') 
            plt.plot(X_plot[:, 0],np.exp(log_dens1),\
                     color=plt.cm.get_cmap(colormap,4).colors[0,:],\
                     zorder=4,linewidth=3) 
        except:
            pass
        try:
            kde2 = KernelDensity(kernel=ker,bandwidth=bw2vol).fit(kdedata_SHAPvol_2)
            log_dens2 = kde2.score_samples(X_plot)
            plt.fill_between(X_plot[:, 0],np.exp(log_dens2),y2=0,alpha=alphval,\
                             fc=plt.cm.get_cmap(colormap,4).colors[1,:],\
                             zorder=1,label='Ejection')
            plt.plot(X_plot[:, 0],np.exp(log_dens2),\
                     color=plt.cm.get_cmap(colormap,4).colors[1,:],\
                     zorder=5,linewidth=3)
        except:
            pass
        try:
            kde3 = KernelDensity(kernel=ker,bandwidth=bw3vol).fit(kdedata_SHAPvol_3)
            log_dens3 = kde3.score_samples(X_plot)
            plt.fill_between(X_plot[:, 0],np.exp(log_dens3),y2=0,alpha=alphval,\
                             fc=plt.cm.get_cmap(colormap,4).colors[2,:],\
                             zorder=2,label='Inward\ninteraction')
            plt.plot(X_plot[:, 0],np.exp(log_dens3),\
                     color=plt.cm.get_cmap(colormap,4).colors[2,:],\
                     zorder=6,linewidth=3)
        except:
            pass
        try:
            kde4 = KernelDensity(kernel=ker,bandwidth=bw4vol).fit(kdedata_SHAPvol_4)
            log_dens4 = kde4.score_samples(X_plot)
            plt.fill_between(X_plot[:, 0],np.exp(log_dens4),y2=0,alpha=alphval,\
                             fc=plt.cm.get_cmap(colormap,4).colors[3,:],\
                             zorder=3,label='Sweep')
            plt.plot(X_plot[:, 0],np.exp(log_dens4),\
                     color=plt.cm.get_cmap(colormap,4).colors[3,:],\
                     zorder=7,linewidth=3)
        except:
            pass
        ax.set_xlabel(self.ylabel_shap_vol,fontsize=20)
        ax.set_ylabel('Normalized Density',fontsize=20)
        plt.tick_params(axis='both', which='major', labelsize=20)   
        ax.set_position([0.15,0.2,0.55,0.65]) 
        ax.tick_params(axis='both', which='major', labelsize=20)
        ax.ticklabel_format(style='sci',scilimits=(0,2))
        ax.xaxis.get_offset_text().set_fontsize(20)
        plt.yscale('log')
        ax.set_ylim([1e-5,1e0])
        plt.legend(fontsize=20, bbox_to_anchor=(1, 1))
        ax.grid()
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/kde_SHAPvol_'+colormap+'_30+.png')  
        # New figure
        plt.figure(22,figsize=(10, 5))
        ax = plt.axes()
        alphval = 0.5
        X_plot = np.linspace(self.shapmin,self.shapmax,self.nbars)[:, np.newaxis]
        try:
            kde2 = KernelDensity(kernel=ker,bandwidth=bw2).fit(kdedata_SHAP_2)
            log_dens2 = kde2.score_samples(X_plot)
            plt.fill_between(X_plot[:, 0],np.exp(log_dens2),y2=0,alpha=alphval,\
                             fc=plt.cm.get_cmap(colormap,4).colors[1,:],\
                             zorder=1,label='Ejection')
            plt.plot(X_plot[:, 0],np.exp(log_dens2),\
                     color=plt.cm.get_cmap(colormap,4).colors[1,:],\
                     zorder=5,linewidth=3)
        except:
            pass
        try:
            kde4 = KernelDensity(kernel=ker,bandwidth=bw4).fit(kdedata_SHAP_4)
            log_dens4 = kde4.score_samples(X_plot)
            plt.fill_between(X_plot[:, 0],np.exp(log_dens4),y2=0,alpha=alphval,\
                             fc=plt.cm.get_cmap(colormap,4).colors[3,:],\
                             zorder=3,label='Sweep')
            plt.plot(X_plot[:, 0],np.exp(log_dens4),\
                     color=plt.cm.get_cmap(colormap,4).colors[3,:],\
                     zorder=7,linewidth=3)
        except:
            pass
        try:
            kde13 = KernelDensity(kernel=ker,bandwidth=bw13).fit(kdedata_SHAP_13)
            log_dens13 = kde13.score_samples(X_plot)
            plt.fill_between(X_plot[:, 0],np.exp(log_dens13),y2=0,alpha=alphval,\
                             fc='black',\
                             zorder=3,label='Inward+\nOutward\ninteractions')
            plt.plot(X_plot[:, 0],np.exp(log_dens13),\
                     color='black',\
                     zorder=7,linewidth=3)
        except:
            pass
        ax.set_xlabel(self.ylabel_shap,fontsize=20)
        ax.set_ylabel('Normalized Density',fontsize=20)
        plt.tick_params(axis='both', which='major', labelsize=20)   
        ax.set_position([0.15,0.2,0.55,0.65]) 
        ax.tick_params(axis='both', which='major', labelsize=20)
        ax.ticklabel_format(style='sci',scilimits=(0,2))
        ax.xaxis.get_offset_text().set_fontsize(20)
        plt.yscale('log')
        ax.set_ylim([1e-5,1e1])
        plt.legend(fontsize=20, bbox_to_anchor=(1, 1))
        ax.grid() 
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/kde_SHAPjoin_'+colormap+'_30+.png')
        # New figure
        plt.figure(23,figsize=(10, 5))
        ax = plt.axes()
        alphval = 0.5
        X_plot = np.linspace(self.shapminvol,self.shapmaxvol,self.nbars)[:, np.newaxis]
        try:
            kde2 = KernelDensity(kernel=ker,bandwidth=bw2vol).fit(kdedata_SHAPvol_2)
            log_dens2 = kde2.score_samples(X_plot)
            plt.fill_between(X_plot[:, 0],np.exp(log_dens2),y2=0,alpha=alphval,\
                             fc=plt.cm.get_cmap(colormap,4).colors[1,:],\
                             zorder=1,label='Ejection')
            plt.plot(X_plot[:, 0],np.exp(log_dens2),\
                     color=plt.cm.get_cmap(colormap,4).colors[1,:],\
                     zorder=5,linewidth=3)
        except:
            pass
        try:
            kde4 = KernelDensity(kernel=ker,bandwidth=bw4vol).fit(kdedata_SHAPvol_4)
            log_dens4 = kde4.score_samples(X_plot)
            plt.fill_between(X_plot[:, 0],np.exp(log_dens4),y2=0,alpha=alphval,\
                             fc=plt.cm.get_cmap(colormap,4).colors[3,:],\
                             zorder=3,label='Sweep')
            plt.plot(X_plot[:, 0],np.exp(log_dens4),\
                     color=plt.cm.get_cmap(colormap,4).colors[3,:],\
                     zorder=7,linewidth=3)
        except:
            pass
        try:
            kde13 = KernelDensity(kernel=ker,bandwidth=bw13vol).fit(kdedata_SHAPvol_13)
            log_dens13 = kde13.score_samples(X_plot)
            plt.fill_between(X_plot[:, 0],np.exp(log_dens13),y2=0,alpha=alphval,\
                             fc='black',\
                             zorder=3,label='Inward+\nOutward\ninteractions')
            plt.plot(X_plot[:, 0],np.exp(log_dens13),\
                     color='black',\
                     zorder=7,linewidth=3)
        except:
            pass
        ax.set_xlabel(self.ylabel_shap_vol,fontsize=20)
        ax.set_ylabel('Normalized Density',fontsize=20)
        plt.tick_params(axis='both', which='major', labelsize=20)   
        ax.set_position([0.15,0.2,0.55,0.65]) 
        ax.tick_params(axis='both', which='major', labelsize=20)
        ax.ticklabel_format(style='sci',scilimits=(0,2))
        ax.xaxis.get_offset_text().set_fontsize(20)
        plt.yscale('log')
        ax.set_ylim([1e-5,1e0])
        plt.legend(fontsize=20, bbox_to_anchor=(1, 1))
        ax.grid()  
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/kde_SHAPvoljoin_'+colormap+'_30+.png')
        
        
            
    def plot_shaps_AR(self,colormap='viridis'):
        """ 
        Function for plotting the results of the SHAP vs the Reynolds stress
        """

        import matplotlib.pyplot as plt
        import matplotlib.colors as colors
        from matplotlib import cm  
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/')
        except:
            pass
        cmap = cm.get_cmap('viridis', 4).colors
        fs = 20
        fig = plt.figure()
        ax = plt.axes()
        plt.plot(self.AR1_grid,self.SHAP_grid1*1e3,\
                   color=cmap[0,:],linewidth=5,label='Outward interactions')
        plt.plot(self.AR1_grid,self.SHAP_grid2*1e3,\
                   color=cmap[1,:],linewidth=5,label='Ejections') 
        plt.plot(self.AR1_grid,self.SHAP_grid3*1e3,\
                   color=cmap[2,:],linewidth=5,label='Inward interactions')
        plt.plot(self.AR1_grid,self.SHAP_grid4*1e3,\
                   color=cmap[3,:],linewidth=5,label='Sweeps')
        plt.legend(fontsize=fs-6)
        plt.grid()
        plt.ylim([0,2])
        plt.xlim([0.1,20])
        plt.xlabel('$\Delta x/\Delta y$',fontsize=fs)
        plt.ylabel('$|\phi_i| \cdot 10^{-3}$',fontsize=fs)
        plt.xscale('log')
        plt.tick_params(axis='both',which='major',labelsize=fs)
        plt.tick_params(axis='both',which='major',labelsize=fs)
        plt.tight_layout()
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/SHAP_AR_'+colormap+'_30+.png')
        fig = plt.figure()
        ax = plt.axes()
        plt.plot(self.AR1_grid,self.SHAP_grid1vol*1e9,\
                   color=cmap[0,:],linewidth=5,label='Outward interactions')
        plt.plot(self.AR1_grid,self.SHAP_grid2vol*1e9,\
                   color=cmap[1,:],linewidth=5,label='Ejections') 
        plt.plot(self.AR1_grid,self.SHAP_grid3vol*1e9,\
                   color=cmap[2,:],linewidth=5,label='Inward interactions')
        plt.plot(self.AR1_grid,self.SHAP_grid4vol*1e9,\
                   color=cmap[3,:],linewidth=5,label='Sweeps')
        plt.legend(fontsize=fs-6)
        plt.grid()
        plt.ylim([0,15])
        plt.xlim([0.1,20])
        plt.xlabel('$\Delta x/\Delta y$',fontsize=fs)
        plt.ylabel('$\phi_i /S^+ \cdot 10^{-9}$',fontsize=fs)
        plt.xscale('log')
        plt.tick_params(axis='both',which='major',labelsize=fs)
        plt.tick_params(axis='both',which='major',labelsize=fs)
        plt.tight_layout()
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/SHAPvol_AR_'+colormap+'_30+.png')
       

    def plot_shaps_AR_scatter(self,colormap='viridis'):
        """ 
        Function for plotting the results of the SHAP vs the aspect ratio
        """
        import matplotlib.pyplot as plt
        import matplotlib as mpl
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/')
        except:
            pass
        fs = 20
        fig = plt.figure()
        ax = plt.axes()
        if self.wallattach:
            plt.scatter(self.dxdy_wa,self.shap_wa,c=self.event_wa,marker='o',\
                        linewidths=0.5,edgecolors='black',s=100,\
                        cmap=plt.cm.get_cmap(colormap,4),vmin=1,vmax=4)
        plt.scatter(self.dxdy_wd,self.shap_wd,c=self.event_wd,marker='s',\
                    linewidths=0.5,edgecolors='black',s=100,\
                    cmap=plt.cm.get_cmap(colormap,4),vmin=1,vmax=4)
        plt.grid()
        plt.xlabel('$\Delta x/\Delta y$',fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        plt.xscale('log')
        plt.tick_params(axis='both', which='major', labelsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        handles = [mpl.lines.Line2D([0],[0],marker='o',markerfacecolor='w',\
                                    markeredgecolor='k',markersize=1, ls=''),\
                   mpl.lines.Line2D([0],[0],marker='s',markerfacecolor='w',\
                                    markeredgecolor='k',markersize=1, ls='')]
        labels= ['W-A','W-D']
        if self.wallattach:
            plt.legend(handles,labels,fontsize=fs,markerscale=10) 
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(ticks=[1,2,3,4],cax = cbaxes)
        cb.ax.set_yticklabels(['Outward\ninteraction','Ejection',\
                               'Inward\ninteraction','Sweep'],fontsize=fs-4)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/dxdy_SHAP_'+colormap+'_30+.png')
        fig = plt.figure()
        ax = plt.axes()
        if self.wallattach:
            plt.scatter(self.dxdy_wa,self.shap_wa_vol,c=self.event_wa,marker='o',\
                        linewidths=0.5,edgecolors='black',s=100,\
                        cmap=plt.cm.get_cmap(colormap,4),vmin=1,vmax=4)
        plt.scatter(self.dxdy_wd,self.shap_wd_vol,c=self.event_wd,marker='s',\
                    linewidths=0.5,edgecolors='black',s=100,\
                    cmap=plt.cm.get_cmap(colormap,4),vmin=1,vmax=4)
        plt.grid()
        plt.xlabel('$\Delta x/\Delta y$',fontsize=fs)
        plt.ylabel(self.ylabel_shap_vol,fontsize=fs)
        plt.xscale('log')
        plt.tick_params(axis='both', which='major', labelsize=fs)
        ax.set_position([0.2,0.2,0.5,0.65]) 
        handles = [mpl.lines.Line2D([0],[0],marker='o',markerfacecolor='w',\
                                    markeredgecolor='k',markersize=1, ls=''),\
                   mpl.lines.Line2D([0],[0],marker='s',markerfacecolor='w',\
                                    markeredgecolor='k',markersize=1, ls='')]
        labels= ['W-A','W-D']
        if self.wallattach:
            plt.legend(handles,labels,fontsize=fs,markerscale=10) 
        cbaxes = fig.add_axes([0.75, 0.15, 0.02, 0.7])
        cb = plt.colorbar(ticks=[1,2,3,4],cax = cbaxes)
        cb.ax.set_yticklabels(['Outward\ninteraction','Ejection',\
                               'Inward\ninteraction','Sweep'],fontsize=fs-4)
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/dxdy_SHAPvol_'+colormap+'_30+.png')
           
        
                
    def plot_shaps_AR_pdf(self,colormap='viridis',bin_num=50,lev_val=5,alf=0.5):
        """ 
        Function for plotting the results of the SHAP vs the Reynolds stress
        """
        import matplotlib.pyplot as plt
        import matplotlib as mpl    
        from scipy.interpolate import interp2d
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/')
        except:
            pass
        xhistmin = np.log10(np.min([np.min(self.dxdy_1),np.min(self.dxdy_2),np.min(self.dxdy_3),np.min(self.dxdy_4)])/1.2)
        xhistmax = np.log10(np.max([np.max(self.dxdy_1),np.max(self.dxdy_2),np.max(self.dxdy_3),np.max(self.dxdy_4)])*1.2)
        yhistmin = np.min([np.min(self.shap_1),np.min(self.shap_2),np.min(self.shap_3),np.min(self.shap_4)])/1.2
        yhistmax = np.max([np.max(self.shap_1),np.max(self.shap_2),np.max(self.shap_3),np.max(self.shap_4)])*1.2
        if np.isinf(xhistmin):
            xhistmin = -5
        elif np.isinf(yhistmin):
            yhistmin = -5
        histogram1,dxdy_value1,shap_value1 = np.histogram2d(np.log10(self.dxdy_1),self.shap_1,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram2,dxdy_value2,shap_value2 = np.histogram2d(np.log10(self.dxdy_2),self.shap_2,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram3,dxdy_value3,shap_value3 = np.histogram2d(np.log10(self.dxdy_3),self.shap_3,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram4,dxdy_value4,shap_value4 = np.histogram2d(np.log10(self.dxdy_4),self.shap_4,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        dxdy_value1 = dxdy_value1[:-1]+np.diff(dxdy_value1)/2
        shap_value1 = shap_value1[:-1]+np.diff(shap_value1)/2
        dxdy_value2 = dxdy_value2[:-1]+np.diff(dxdy_value2)/2
        shap_value2 = shap_value2[:-1]+np.diff(shap_value2)/2
        dxdy_value3 = dxdy_value3[:-1]+np.diff(dxdy_value3)/2
        shap_value3 = shap_value3[:-1]+np.diff(shap_value3)/2
        dxdy_value4 = dxdy_value4[:-1]+np.diff(dxdy_value4)/2
        shap_value4 = shap_value4[:-1]+np.diff(shap_value4)/2
        min_dxdy = np.min([dxdy_value1,dxdy_value2,dxdy_value3,dxdy_value4])
        max_dxdy = np.max([dxdy_value1,dxdy_value2,dxdy_value3,dxdy_value4])
        min_shap = np.min([shap_value1,shap_value2,shap_value3,shap_value4])
        max_shap = np.max([shap_value1,shap_value2,shap_value3,shap_value4])
        interp_h1 = interp2d(dxdy_value1,shap_value1,histogram1)
        interp_h2 = interp2d(dxdy_value2,shap_value2,histogram2)
        interp_h3 = interp2d(dxdy_value3,shap_value3,histogram3)
        interp_h4 = interp2d(dxdy_value4,shap_value4,histogram4)
        vec_dxdy = np.linspace(min_dxdy,max_dxdy,1000)
        vec_shap = np.linspace(min_shap,max_shap,1000)
        dxdy_grid,shap_grid = np.meshgrid(vec_dxdy,vec_shap)
        histogram_Q1 = interp_h1(vec_dxdy,vec_shap)
        histogram_Q2 = interp_h2(vec_dxdy,vec_shap)
        histogram_Q3 = interp_h3(vec_dxdy,vec_shap)
        histogram_Q4 = interp_h4(vec_dxdy,vec_shap)
        dxdy_gridp = 10**dxdy_grid
        fs = 20
        plt.figure()
        color11 = plt.cm.get_cmap(colormap,4).colors[0,0]
        color12 = plt.cm.get_cmap(colormap,4).colors[0,1]
        color13 = plt.cm.get_cmap(colormap,4).colors[0,2]
        color21 = plt.cm.get_cmap(colormap,4).colors[1,0]
        color22 = plt.cm.get_cmap(colormap,4).colors[1,1]
        color23 = plt.cm.get_cmap(colormap,4).colors[1,2]
        color31 = plt.cm.get_cmap(colormap,4).colors[2,0]
        color32 = plt.cm.get_cmap(colormap,4).colors[2,1]
        color33 = plt.cm.get_cmap(colormap,4).colors[2,2]
        color41 = plt.cm.get_cmap(colormap,4).colors[3,0]
        color42 = plt.cm.get_cmap(colormap,4).colors[3,1]
        color43 = plt.cm.get_cmap(colormap,4).colors[3,2]
        plt.contourf(dxdy_gridp,shap_grid,histogram_Q1.T,levels=[lev_val,1e5*lev_val],colors=[(color11,color12,color13)],alpha=alf)
        plt.contourf(dxdy_gridp,shap_grid,histogram_Q2.T,levels=[lev_val,1e5*lev_val],colors=[(color21,color22,color23)],alpha=alf)
        plt.contourf(dxdy_gridp,shap_grid,histogram_Q3.T,levels=[lev_val,1e5*lev_val],colors=[(color31,color32,color33)],alpha=alf)
        plt.contourf(dxdy_gridp,shap_grid,histogram_Q4.T,levels=[lev_val,1e5*lev_val],colors=[(color41,color42,color43)],alpha=alf)
        plt.contour(dxdy_gridp,shap_grid,histogram_Q1.T,levels=[lev_val],colors=[(color11,color12,color13)])
        plt.contour(dxdy_gridp,shap_grid,histogram_Q2.T,levels=[lev_val],colors=[(color21,color22,color23)])
        plt.contour(dxdy_gridp,shap_grid,histogram_Q3.T,levels=[lev_val],colors=[(color31,color32,color33)])
        plt.contour(dxdy_gridp,shap_grid,histogram_Q4.T,levels=[lev_val],colors=[(color41,color42,color43)])
        plt.xlim([0.1,100])
        plt.ylim([0,30])
        plt.xscale('log')
        plt.grid()
        plt.xlabel('$\Delta x/\Delta y$',\
                   fontsize=fs)
        plt.ylabel(self.ylabel_shap,fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        handles = [mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color11,color12,color13,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color11,color12,color13,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color21,color22,color23,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color21,color22,color23,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color31,color32,color33,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color31,color32,color33,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color41,color42,color43,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color41,color42,color43,alf))]
        labels= ['Outward\ninteractions','Ejections','Inward\ninteractions','Sweeps']
        plt.legend(handles,labels,fontsize=fs-4,loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_AR_SHAP_'+colormap+'_30+.png')
        xhistmin = np.log10(np.min([np.min(self.dxdy_1),np.min(self.dxdy_2),np.min(self.dxdy_3),np.min(self.dxdy_4)])/1.2)
        xhistmax = np.log10(np.max([np.max(self.dxdy_1),np.max(self.dxdy_2),np.max(self.dxdy_3),np.max(self.dxdy_4)])*1.2)
        yhistmin = np.min([np.min(self.shap_1_vol),np.min(self.shap_2_vol),np.min(self.shap_3_vol),np.min(self.shap_4_vol)])/1.2
        yhistmax = np.max([np.max(self.shap_1_vol),np.max(self.shap_2_vol),np.max(self.shap_3_vol),np.max(self.shap_4_vol)])*1.2
        if np.isinf(xhistmin):
            xhistmin = -5
        elif np.isinf(yhistmin):
            yhistmin = -5
        histogram1_vol,dxdy_value1_vol,shap_value1_vol = np.histogram2d(np.log10(self.dxdy_1),self.shap_1_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram2_vol,dxdy_value2_vol,shap_value2_vol = np.histogram2d(np.log10(self.dxdy_2),self.shap_2_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram3_vol,dxdy_value3_vol,shap_value3_vol = np.histogram2d(np.log10(self.dxdy_3),self.shap_3_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        histogram4_vol,dxdy_value4_vol,shap_value4_vol = np.histogram2d(np.log10(self.dxdy_4),self.shap_4_vol,bins=bin_num,range=[[xhistmin,xhistmax],[yhistmin,yhistmax]])
        dxdy_value1_vol = dxdy_value1_vol[:-1]+np.diff(dxdy_value1_vol)/2
        shap_value1_vol = shap_value1_vol[:-1]+np.diff(shap_value1_vol)/2
        dxdy_value2_vol = dxdy_value2_vol[:-1]+np.diff(dxdy_value2_vol)/2
        shap_value2_vol = shap_value2_vol[:-1]+np.diff(shap_value2_vol)/2
        dxdy_value3_vol = dxdy_value3_vol[:-1]+np.diff(dxdy_value3_vol)/2
        shap_value3_vol = shap_value3_vol[:-1]+np.diff(shap_value3_vol)/2
        dxdy_value4_vol = dxdy_value4_vol[:-1]+np.diff(dxdy_value4_vol)/2
        shap_value4_vol = shap_value4_vol[:-1]+np.diff(shap_value4_vol)/2
        min_dxdy_vol = np.min([dxdy_value1_vol,dxdy_value2_vol,dxdy_value3_vol,dxdy_value4_vol])
        max_dxdy_vol = np.max([dxdy_value1_vol,dxdy_value2_vol,dxdy_value3_vol,dxdy_value4_vol])
        min_shap_vol = np.min([shap_value1_vol,shap_value2_vol,shap_value3_vol,shap_value4_vol])
        max_shap_vol = np.max([shap_value1_vol,shap_value2_vol,shap_value3_vol,shap_value4_vol])
        interp_h1_vol = interp2d(dxdy_value1_vol,shap_value1_vol,histogram1_vol)
        interp_h2_vol = interp2d(dxdy_value2_vol,shap_value2_vol,histogram2_vol)
        interp_h3_vol = interp2d(dxdy_value3_vol,shap_value3_vol,histogram3_vol)
        interp_h4_vol = interp2d(dxdy_value4_vol,shap_value4_vol,histogram4_vol)
        vec_dxdy_vol = np.linspace(min_dxdy_vol,max_dxdy_vol,1000)
        vec_shap_vol = np.linspace(min_shap_vol,max_shap_vol,1000)
        dxdy_grid_vol,shap_grid_vol = np.meshgrid(vec_dxdy_vol,vec_shap_vol)
        histogram_Q1_vol = interp_h1_vol(vec_dxdy_vol,vec_shap_vol)
        histogram_Q2_vol = interp_h2_vol(vec_dxdy_vol,vec_shap_vol)
        histogram_Q3_vol = interp_h3_vol(vec_dxdy_vol,vec_shap_vol)
        histogram_Q4_vol = interp_h4_vol(vec_dxdy_vol,vec_shap_vol)
        fs = 20
        plt.figure()
        color11 = plt.cm.get_cmap(colormap,4).colors[0,0]
        color12 = plt.cm.get_cmap(colormap,4).colors[0,1]
        color13 = plt.cm.get_cmap(colormap,4).colors[0,2]
        color21 = plt.cm.get_cmap(colormap,4).colors[1,0]
        color22 = plt.cm.get_cmap(colormap,4).colors[1,1]
        color23 = plt.cm.get_cmap(colormap,4).colors[1,2]
        color31 = plt.cm.get_cmap(colormap,4).colors[2,0]
        color32 = plt.cm.get_cmap(colormap,4).colors[2,1]
        color33 = plt.cm.get_cmap(colormap,4).colors[2,2]
        color41 = plt.cm.get_cmap(colormap,4).colors[3,0]
        color42 = plt.cm.get_cmap(colormap,4).colors[3,1]
        color43 = plt.cm.get_cmap(colormap,4).colors[3,2]
        dxdy_gridp_vol = 10**dxdy_grid_vol
        plt.contourf(dxdy_gridp_vol,shap_grid_vol,histogram_Q1_vol.T,levels=[lev_val,1e5*lev_val],colors=[(color11,color12,color13)],alpha=alf)
        plt.contourf(dxdy_gridp_vol,shap_grid_vol,histogram_Q2_vol.T,levels=[lev_val,1e5*lev_val],colors=[(color21,color22,color23)],alpha=alf)
        plt.contourf(dxdy_gridp_vol,shap_grid_vol,histogram_Q3_vol.T,levels=[lev_val,1e5*lev_val],colors=[(color31,color32,color33)],alpha=alf)
        plt.contourf(dxdy_gridp_vol,shap_grid_vol,histogram_Q4_vol.T,levels=[lev_val,1e5*lev_val],colors=[(color41,color42,color43)],alpha=alf)
        plt.contour(dxdy_gridp_vol,shap_grid_vol,histogram_Q1_vol.T,levels=[lev_val],colors=[(color11,color12,color13)])
        plt.contour(dxdy_gridp_vol,shap_grid_vol,histogram_Q2_vol.T,levels=[lev_val],colors=[(color21,color22,color23)])
        plt.contour(dxdy_gridp_vol,shap_grid_vol,histogram_Q3_vol.T,levels=[lev_val],colors=[(color31,color32,color33)])
        plt.contour(dxdy_gridp_vol,shap_grid_vol,histogram_Q4_vol.T,levels=[lev_val],colors=[(color41,color42,color43)])
        plt.xlim([0.05,50])
        plt.ylim([0,30])
        plt.xscale('log')
        plt.grid()
        plt.xlabel('$\Delta x/\Delta y$',\
                   fontsize=fs)
        plt.ylabel(self.ylabel_shap_vol,fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)
        handles = [mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color11,color12,color13,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color11,color12,color13,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color21,color22,color23,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color21,color22,color23,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color31,color32,color33,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color31,color32,color33,alf)),\
                   mpl.lines.Line2D([0],[0],marker='o',markeredgecolor=(color41,color42,color43,1),markersize=15, ls='',markeredgewidth=1,markerfacecolor=(color41,color42,color43,alf))]
        labels= ['Outward\ninteractions','Ejections','Inward\ninteractions','Sweeps']
        plt.legend(handles,labels,fontsize=fs-4,loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/hist2d_interp_AR_SHAPvol_'+colormap+'_30+.png')
        
        
        
          
    def plot_shaps_total(self,colormap='viridis'):
        """
        Function for calculating the SHAP contribution of each kind of 
        structure
        """
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/')
        except:
            pass
        shap1 = self.shap1cum
        shap2 = self.shap2cum
        shap3 = self.shap3cum
        shap4 = self.shap4cum
        shapb = self.shapbcum
        shap_vol1 = self.shap_vol1cum
        shap_vol2 = self.shap_vol2cum
        shap_vol3 = self.shap_vol3cum
        shap_vol4 = self.shap_vol4cum
        shap_volb = self.shap_volbcum
        shap_sum = shap1+shap2+shap3+shap4+shapb
        shap_vol_sum = shap_vol1+shap_vol2+shap_vol3+shap_vol4+shap_volb
        shap1 /= shap_sum
        shap2 /= shap_sum
        shap3 /= shap_sum
        shap4 /= shap_sum
        shapb /= shap_sum
        shap_vol1 /= shap_vol_sum
        shap_vol2 /= shap_vol_sum
        shap_vol3 /= shap_vol_sum
        shap_vol4 /= shap_vol_sum
        shap_volb /= shap_vol_sum
        import matplotlib.pyplot as plt
        fs = 20
        plt.figure()
        ax = plt.axes()
        plt.bar([0.5,1.5],[shap1,shap_vol1],\
                color=plt.cm.get_cmap(colormap,4).colors[0,:],\
                label='Outward\ninteraction',edgecolor='black')
        plt.bar([0.5,1.5],[shap2,shap_vol2],bottom=[shap1,shap_vol1],\
                color=plt.cm.get_cmap(colormap,4).colors[1,:],\
                label='Ejection',edgecolor='black')
        plt.bar([0.5,1.5],[shap3,shap_vol3],\
                bottom=[shap1+shap2,shap_vol1+shap_vol2],\
                color=plt.cm.get_cmap(colormap,4).colors[2,:],\
                label='Inward\ninteraction',edgecolor='black')
        plt.bar([0.5,1.5],[shap4,shap_vol4],bottom=[shap1+shap2+shap3,\
                shap_vol1+shap_vol2+shap_vol3],\
        color=plt.cm.get_cmap(colormap,4).colors[3,:],\
                label='Sweeps',edgecolor='black')
        plt.bar([0.5,1.5],[shapb,shap_volb],bottom=[shap1+shap2+shap3+shap4,\
                shap_vol1+shap_vol2+shap_vol3+shap_vol4],edgecolor='black',\
                label='Background',fill=False)
        ax.set_ylabel('Fraction of the total',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)   
        ax.set_position([0.2,0.2,0.35,0.65]) 
        ax.tick_params(axis='both', which='major', labelsize=fs)
        ax.set_xticks([0.5,1.5])
        ax.set_xticklabels(['$\Phi_e/\Phi_T$','$\Phi^V_e/\Phi^V_T$'])
        ax.xaxis.get_offset_text().set_fontsize(fs)
        plt.legend(fontsize=fs, bbox_to_anchor=(1, 1))
        ax.grid()  
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/bar_SHAP_'+colormap+'_30+.png')
        file_save = open('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/bar_SHAP.txt', "w+") 
        file_save.write('SHAP percentage: \nOutward Int. '+str(shap1)+\
                        '\nEjections '+str(shap2)+'\nInward Int. '+str(shap3)+\
                        '\nSweeps '+str(shap4)+'\n')
        file_save.write('SHAP per volume percentage: \nOutward Int. '+\
                        str(shap_vol1)+'\nEjections '+str(shap_vol2)+\
                        '\nInward Int. '+str(shap_vol3)+'\nSweeps '+\
                        str(shap_vol4)+'\n')
        file_save.close()
            
            
          
    def plot_shaps_total_noback(self,start=1,end=2,step=1,\
                                file='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/SHAP_fields_io/vel_',\
                                fileQ='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Q_fields_io/vel_',\
                                fileuvw='/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newdata/hdf5/vel_',\
                                filenorm="norm.txt",\
                                colormap='viridis',absolute=False,testcases=False,\
                                filetest='ind_val.txt',numfield=-1,fieldini=0,dx=1,dy=1,\
                                volfilt=1e8):
        """
        Function for calculating the SHAP contribution of each kind of 
        structure
        """
        try:
            os.mkdir('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/')
        except:
            pass
        shap1 = self.shap1cum
        shap2 = self.shap2cum
        shap3 = self.shap3cum
        shap4 = self.shap4cum
        shap_vol1 = self.shap_vol1cum
        shap_vol2 = self.shap_vol2cum
        shap_vol3 = self.shap_vol3cum
        shap_vol4 = self.shap_vol4cum
        shap_sum = shap1+shap2+shap3+shap4
        shap_vol_sum = shap_vol1+shap_vol2+shap_vol3+shap_vol4
        shap1 /= shap_sum
        shap2 /= shap_sum
        shap3 /= shap_sum
        shap4 /= shap_sum
        shap_vol1 /= shap_vol_sum
        shap_vol2 /= shap_vol_sum
        shap_vol3 /= shap_vol_sum
        shap_vol4 /= shap_vol_sum
        import matplotlib.pyplot as plt
        fs = 20
        plt.figure()
        ax = plt.axes()
        plt.bar([0.5,1.5],[shap1,shap_vol1],\
                color=plt.cm.get_cmap(colormap,4).colors[0,:],\
                label='Outward\ninteraction',edgecolor='black')
        plt.bar([0.5,1.5],[shap2,shap_vol2],bottom=[shap1,shap_vol1],\
                color=plt.cm.get_cmap(colormap,4).colors[1,:],\
                label='Ejection',edgecolor='black')
        plt.bar([0.5,1.5],[shap3,shap_vol3],\
                bottom=[shap1+shap2,shap_vol1+shap_vol2],\
                color=plt.cm.get_cmap(colormap,4).colors[2,:],\
                label='Inward\ninteraction',edgecolor='black')
        plt.bar([0.5,1.5],[shap4,shap_vol4],bottom=[shap1+shap2+shap3,\
                shap_vol1+shap_vol2+shap_vol3],\
        color=plt.cm.get_cmap(colormap,4).colors[3,:],\
                label='Sweeps',edgecolor='black')
        ax.set_ylabel('Fraction of the total',fontsize=fs)
        plt.tick_params(axis='both', which='major', labelsize=fs)   
        ax.set_position([0.2,0.2,0.35,0.65]) 
        ax.tick_params(axis='both', which='major', labelsize=fs)
        ax.set_xticks([0.5,1.5])
        ax.set_xticklabels(['$\Phi_e/\Phi_T$','$\Phi^V_e/\Phi^V_T$'])
        ax.xaxis.get_offset_text().set_fontsize(fs)
        plt.legend(fontsize=fs, bbox_to_anchor=(1, 1))
        ax.grid()  
        plt.savefig('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/bar_SHAP_noback_'+colormap+'_30+.png')
        file_save = open('/codebase/python files/Identifying-regions-of-importance-in-wall-bounded-turbulence-through-explainable-deep-learning-main/newresults/Experiment_2d/bar_SHAP_noback.txt', "w+") 
        file_save.write('SHAP percentage: \nOutward Int. '+str(shap1)+\
                        '\nEjections '+str(shap2)+'\nInward Int. '+str(shap3)+\
                        '\nSweeps '+str(shap4)+'\n')
        file_save.write('SHAP per volume percentage: \nOutward Int. '+\
                        str(shap_vol1)+'\nEjections '+str(shap_vol2)+\
                        '\nInward Int. '+str(shap_vol3)+'\nSweeps '+\
                        str(shap_vol4)+'\n')
        file_save.close()            
            
            