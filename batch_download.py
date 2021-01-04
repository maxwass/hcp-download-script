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
lr_msmall = "rfMRI_REST1_LR_Atlas_MSMAll_hp2000_clean.dtseries.nii"
rl_msmall = "rfMRI_REST1_RL_Atlas_MSMAll_hp2000_clean.dtseries.nii"

lr_no_msmall = "rfMRI_REST1_LR_Atlas_hp2000_clean.dtseries.nii"
rl_no_msmall = "rfMRI_REST1_RL_Atlas_hp2000_clean.dtseries.nii"

lr_msmall_hcp_rel_path = "/MNINonLinear/Results/rfMRI_REST1_LR/" + lr_msmall
rl_msmall_hcp_rel_path = "/MNINonLinear/Results/rfMRI_REST1_RL/" + rl_msmall

lr_no_msmall_hcp_rel_path = "/MNINonLinear/Results/rfMRI_REST1_LR/" + lr_no_msmall
rl_no_msmall_hcp_rel_path = "/MNINonLinear/Results/rfMRI_REST1_RL/" + rl_no_msmall

#"HCP_1200/996782/MNINonLinear/Results/rfMRI_REST1_RL/rfMRI_REST1_RL_Atlas_hp2000_clean.dtseries.nii"


atlas_file_pre  = "/MNINonLinear/fsaverage_LR32k/"
detrieux_atlas_file_post = ".aparc.a2009s.32k_fs_LR.dlabel.nii"
desikan_atlas_file_post = ".aparc.32k_fs_LR.dlabel.nii"

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

    #msall
    hcp_path = path2HCP_1200 + patient_id + lr_msmall_hcp_rel_path
    readable_name = "LR_msmall"
    local_path = subject_dir + "/" + lr_msmall
    files.append({"hcp_path": hcp_path, "readable_name": readable_name, "local_path": local_path})

    hcp_path = path2HCP_1200 + patient_id + rl_msmall_hcp_rel_path
    readable_name = "RL_msmall"
    local_path = subject_dir + "/" + rl_msmall
    files.append({"hcp_path": hcp_path, "readable_name": readable_name, "local_path": local_path})

    #no msall
    hcp_path = path2HCP_1200 + patient_id + lr_no_msmall_hcp_rel_path
    readable_name = "LR_no_msmall"
    local_path = subject_dir + "/" + lr_no_msmall
    files.append({"hcp_path": hcp_path, "readable_name": readable_name, "local_path": local_path})

    hcp_path = path2HCP_1200 + patient_id + rl_no_msmall_hcp_rel_path
    readable_name = "RL_no_msmall"
    local_path = subject_dir + "/" + rl_no_msmall
    files.append({"hcp_path": hcp_path, "readable_name": readable_name, "local_path": local_path})


    hcp_path = path2HCP_1200 + patient_id + atlas_file_pre + patient_id + detrieux_atlas_file_post
    readable_name = "Destrieux_aparc32k"
    local_path = subject_dir + "/" + patient_id + detrieux_atlas_file_post
    files.append({"hcp_path": hcp_path, "readable_name": readable_name, "local_path": local_path})

    hcp_path = path2HCP_1200 + patient_id + atlas_file_pre + patient_id + desikan_atlas_file_post
    readable_name = "Desikan_aparc32k"
    local_path = subject_dir + "/" + patient_id + desikan_atlas_file_post
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
        print(f"\n\n{idx}th subject: {subject}")

        #create directory with this subject if it does not exist:
        subject_dir = local_dir+"/"+subject
        Path(subject_dir).mkdir(parents=True, exist_ok=True) #will ignore if exists
        

        #download all files into this dir
        start = time.time()
        for f in list_files(subject):
            #check if file already exists in directory
            #if "no_msmall"  in f["readable_name"]:
            #    input(f'no_small: {f["local_path"]} exist?: {os.path.isfile(f["local_path"])}')
            #elif "msmall"  in f["readable_name"]:
            #    input(f'msmall: {f["local_path"]} exist?: {os.path.isfile(f["local_path"])}')

            if os.path.isfile(f['local_path']):
                print(f'\t{f["readable_name"]} already exists, skipping...')
                continue
            
            #if file does not already exist in local directory, attempt to download it
            print(f'\tdownloading {f["readable_name"]} into {subject_dir}...',end='')
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
        
        #Summarize whats missing
        lr_msmall_miss = patients_missing_file["LR_msmall"]
        rl_msmall_miss = patients_missing_file["RL_msmall"]
        both_msmall_miss = lr_msmall_miss.intersection(rl_msmall_miss)
        lr_len, rl_len, both_len= len(lr_msmall_miss), len(rl_msmall_miss), len(both_msmall_miss)
        print(f"MSMALL missing:    lr {lr_len} | rl {rl_len} | both {both_len}")
        
        lr_no_msmall_miss = patients_missing_file["LR_no_msmall"]
        rl_no_msmall_miss = patients_missing_file["RL_no_msmall"]
        both_no_msmall_miss = lr_no_msmall_miss.intersection(rl_no_msmall_miss)
        lr_len,rl_len,both_len=len(lr_no_msmall_miss),len(rl_no_msmall_miss), len(both_no_msmall_miss)
        print(f"NO_MSMALL missing: lr {lr_len} | rl {rl_len} | both {both_len}")
    

    #End of Download Summary
    print(f"======END OF DOWNLOAD=======")
    print(f"Total Patients: {len(subject_list)}")
    lr_msmall_miss, rl_msmall_miss = patients_missing_file["LR_msmall"],patients_missing_file["RL_msmall"]
    both_msmall_miss = lr_msmall_miss.intersection(rl_msmall_miss)
    lr_len, rl_len, both_len= len(lr_msmall_miss), len(rl_msmall_miss), len(both_msmall_miss)
    print(f"MSMALL missing:    lr {lr_len} | rl {rl_len} | both {both_len}")
    
    lr_no_msmall_miss = patients_missing_file["LR_no_msmall"]
    rl_no_msmall_miss = patients_missing_file["RL_no_msmall"]
    both_no_msmall_miss = lr_no_msmall_miss.intersection(rl_no_msmall_miss)
    lr_len,rl_len,both_len=len(lr_no_msmall_miss),len(rl_no_msmall_miss), len(both_no_msmall_miss)
    print(f"NO_MSMALL missing: lr {lr_len} | rl {rl_len} | both {both_len}")
    
    print(f"DESIKAN missing: {len(patients_missing_file['Desikan_aparc32k'])}")
    print(f"DESTRIE missing: {len(patients_missing_file['Destrieux_aparc32k'])}")
    print(f"======END OF DOWNLOAD=======")
    
    print(f"List of patients with missing files")
    print(f"MSMALL")
    print(f"LR: \n{lr_msmall_miss}")
    print(f"RL: \n{rl_msmall_miss}")
    print(f"BOTH: \n{both_msmall_miss}")
    
    print(f"\nNO MSMALL")
    print(f"LR: same as msmall lr? {lr_msmall==lr_no_small} \n{lr_msmall_miss}")
    print(f"RL: same as msmall rl? {rl_msmall==rl_no_small} \n{rl_no_msmall_miss}")
    print(f"BOTH: same as msmall both? {both_msmall_miss==both_no_msmall_miss} \n{both_no_msmall_miss}")
    
    print(f"\nDESIKAN missing: {patients_missing_file['Desikan_aparc32k']}")
    print(f"DESTRIE missing: {patients_missing_file['Destrieux_aparc32k']}")


#Begin download
download_files()

#save_subject_list_to_mat()

#sl = subject_list_HCP_1200()
#print(f"999th subject_id: {sl[997:1001]}")
