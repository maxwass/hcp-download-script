import os

import subprocess
from pathlib import Path
import datetime

encoding = 'utf-8'

path2HCP_1200 = "/hcp-openaccess/HCP_1200/"


lr_file = "/MNINonLinear/Results/rfMRI_REST1_LR/rfMRI_REST1_LR_Atlas_MSMAll_hp2000_clean.dtseries.nii"
rl_file = "/MNINonLinear/Results/rfMRI_REST1_RL/rfMRI_REST1_RL_Atlas_MSMAll_hp2000_clean.dtseries.nii"

external_hd_path = "/run/media/mwasser6/Elements"
log_file  = external_hd_path + "/download_scripts/log.txt"
local_dir = external_hd_path + "/brain_data"

#raw file location:
# /hcp-openaccess/HCP_1200/100206/MNINonLinear/Results/rfMRI_REST1_RL/rfMRI_REST1_RL_Atlas_MSMAll_hp2000_clean.dtseries.nii

#which files to download
def list_files(patient_id):
    patient_id = str(patient_id)
    files = []
    files.append(path2HCP_1200 + patient_id + lr_file)
    files.append(path2HCP_1200 + patient_id + rl_file)
    return files


#list of subject id's in HCP_1200
def subject_list_HCP_1200():
    #HCP_1200 is 1114 directories, each of which represents a single subject
    #return list of strings, each one representing the subject id of a subject
    args = ["aws s3 ls s3://hcp-openaccess/HCP_1200/"]
    completed_process = subprocess.run(args, capture_output=True, shell=True)
    all_dirs = completed_process.stdout
    dir_list = str.splitlines(all_dirs.decode(encoding))
    subject_list = []

    for subject in dir_list:
        subject_id = subject.split()[1] #remove extranous stuff
        subject_id = subject_id[:-1] #remove trailing '/'
        subject_list.append(subject_id)

    return subject_list

subject_list = subject_list_HCP_1200()

def download_files():

    subject_list = subject_list_HCP_1200()
    for idx, subject in enumerate(subject_list):
        #create directory with this subject id
        subject_dir = local_dir+"/"+subject
        print(f"{idx}th subject: {subject}")
        Path(subject_dir).mkdir(parents=True, exist_ok=True)
        
        #download all files into this dir
        for idx_f, file_to_download in enumerate(list_files(subject)):
            args = ["aws s3 cp s3:/" + file_to_download + " " + subject_dir]
            print(f"downloading {idx_f} into {subject_dir}")
            completed_process = subprocess.run(args, capture_output=True, shell=True)
            
            #if download did not complete properly, not this in log
            if completed_process.returncode != 0:
                with open(log_file,'a') as f:
                    args = ["aws s3 ls s3://hcp-openaccess/HCP_120"]
                    completed_process = subprocess.run(args, capture_output=True, shell=True)
                    f.write(f"\n\n==={idx}th subject: {subject}===\n")
                    f.write(str(datetime.datetime.now())+"\n")
                    f.write(f"Error in downloading {file_to_download}\n")

download_files()

