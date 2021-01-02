#useful resource for aws:
# AWS S3 high level api:
#   https://docs.aws.amazon.com/cli/latest/userguide/cli-services-s3-commands.html

import os
import time
import subprocess
from pathlib import Path
import datetime
from scipy.io import savemat

encoding = 'utf-8'

#relative file path for each patient
lr_file_name = "rfMRI_REST1_LR_Atlas_MSMAll_hp2000_clean.dtseries.nii"
lr_path = "/MNINonLinear/Results/rfMRI_REST1_LR/" + lr_file_name
rl_file_name = "rfMRI_REST1_RL_Atlas_MSMAll_hp2000_clean.dtseries.nii"
rl_path = "/MNINonLinear/Results/rfMRI_REST1_RL/" + rl_file_name

atlas_file_pre  = "/MNINonLinear/fsaverage_LR32k/"
atlas_file_post = ".aparc.a2009s.32k_fs_LR.dlabel.nii"

#paths on aws machine
path2HCP_1200 = "/hcp-openaccess/HCP_1200/"

#paths on local machine
external_hd_path = "/run/media/mwasser6/Elements"
log_file  = external_hd_path + "/download_scripts/log.txt"
local_dir = external_hd_path + "/brain_data"

#raw file location:
# /hcp-openaccess/HCP_1200/100206/MNINonLinear/Results/rfMRI_REST1_RL/rfMRI_REST1_RL_Atlas_MSMAll_hp2000_clean.dtseries.nii


#which files to download
def list_files(patient_id):
    patient_id = str(patient_id)
    files, readable_names = [], []
    files = []
    subject_dir = local_dir+"/"+patient_id

    hcp_path = path2HCP_1200 + patient_id + lr_path
    readable_name = "LR"
    local_path = subject_dir + "/" + lr_file_name
    files.append({"hcp_path": hcp_path, "readable_name": readable_name, "local_path": local_path})

    hcp_path = path2HCP_1200 + patient_id + rl_path
    readable_name = "RL"
    local_path = subject_dir + "/" + rl_file_name
    files.append({"hcp_path": hcp_path, "readable_name": readable_name, "local_path": local_path})
    
    hcp_path = path2HCP_1200 + patient_id + atlas_file_pre + patient_id + atlas_file_post 
    readable_name = "aparc32k"
    local_path = subject_dir + "/" + patient_id + atlas_file_post#[1:] #get rid of beginning '.'
    files.append({"hcp_path": hcp_path, "readable_name": readable_name, "local_path": local_path})
    
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

    for idx, subject in enumerate(dir_list):
        #bug in decoding? 999th Patient (825048) has date/time returned instead of patient_id
        if idx == 999:
            subject_list.append("825048")
            continue
        subject_id = subject.split()[1] #remove extranous stuff
        subject_id = subject_id[:-1] #remove trailing '/'
        subject_list.append(subject_id)

    return subject_list

# https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.savemat.html
def save_subject_list_to_mat():
    subject_list = subject_list_HCP_1200()
    savemat("Allprocessedid.mat", {'subjList': subject_list})

#for each patient, create a local diretory in local_dir and download all files. If there is an issue, write in log file.
def download_files():
    
    #record who is missing which files
    files = list_files('000')
    patients_missing_file = {f["readable_name"]:set() for f in files}

    subject_list = subject_list_HCP_1200()
    for idx, subject in enumerate(subject_list):
        print(f"{idx}th subject: {subject}")

        #create directory with this subject if it does not exist:
        subject_dir = local_dir+"/"+subject
        Path(subject_dir).mkdir(parents=True, exist_ok=True) #will ignore if exists
        

        #download all files into this dir
        start = time.time()
        for f in list_files(subject):
            #check if file already exists in directory
            if os.path.isfile(f['local_path']):
                print(f'{f["readable_name"]} already exists, skipping...')
                continue
            
            #if file does not already exist in local directory, attempt to download it
            print(f'downloading {f["readable_name"]} into {subject_dir}...',end='')
            args = ["aws s3 cp s3:/" + f["hcp_path"] + " " + subject_dir]
            completed_process = subprocess.run(args, capture_output=True, shell=True)
            
            #if download did not complete properly, put this in log
            if completed_process.returncode != 0:
                print(f'ERROR (likely not on server or faulty path given')
                patients_missing_file[f["readable_name"]].add(subject)
                """
                with open(log_file,'a+') as f:
                    f.write(f"\n\n==={idx}th subject: {subject}===\n")
                    f.write(str(datetime.datetime.now())+"\n")
                    f.write(f"Error in downloading {file_to_download}\n")
                    print(f"\tError in downloading {file_to_download}\n")
                """
            else:
                print(f'success')

        end = time.time()
        print(f"Time for download: {(end-start):.1f}")
        
        #Summary of missing thus far
        for f in list_files(subject):
            missing = len(patients_missing_file[f["readable_name"]])
            print(f'Missing {f["readable_name"]}: {missing} |', end='')
        
        lr_missing = patients_missing_file["LR"]
        rl_missing = patients_missing_file["RL"]
        both = lr_missing.intersection(rl_missing)
        print(f'Missing LR and RL: {len(both)}\n\n')
        ##
    
    #Summary of missing thus far
    for readable_file_name in patients_missing_file:
        missing = len(patients_missing_file[readable_file_name])
        print(f'Missing {readable_file_name}: {missing} |', end='')
    
    lr_missing = patients_missing_file["LR"]
    rl_missing = patients_missing_file["RL"]
    both = lr_missing.intersection(rl_missing)
    print(f'Patients with LR Missing": \n\t {lr_missing}')
    print(f'Patients with RL Missing": \n\t {rl_missing}')
    print(f'Patients with BOHT LR and RL Missing": \n\t {both}')

#save_subject_list_to_mat()

#Begin download
download_files()

#sl = subject_list_HCP_1200()
#print(f"999th subject_id: {sl[997:1001]}")
