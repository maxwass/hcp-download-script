#useful resource for aws:
# AWS S3 high level api:
#   https://docs.aws.amazon.com/cli/latest/userguide/cli-services-s3-commands.html

# search for CHANGE for locations of where to customize for new files

import os
import time
import subprocess
from pathlib import Path
import datetime
from scipy.io import savemat

encoding = 'utf-8'

############
#relative file path for each patient:
lr_msmall = "rfMRI_REST1_LR_Atlas_MSMAll_hp2000_clean.dtseries.nii"
rl_msmall = "rfMRI_REST1_RL_Atlas_MSMAll_hp2000_clean.dtseries.nii"

lr_no_msmall = "rfMRI_REST1_LR_Atlas_hp2000_clean.dtseries.nii"
rl_no_msmall = "rfMRI_REST1_RL_Atlas_hp2000_clean.dtseries.nii"

lr_msmall_hcp_rel_path = "/MNINonLinear/Results/rfMRI_REST1_LR/" + lr_msmall
rl_msmall_hcp_rel_path = "/MNINonLinear/Results/rfMRI_REST1_RL/" + rl_msmall

lr_no_msmall_hcp_rel_path = "/MNINonLinear/Results/rfMRI_REST1_LR/" + lr_no_msmall
rl_no_msmall_hcp_rel_path = "/MNINonLinear/Results/rfMRI_REST1_RL/" + rl_no_msmall

#"HCP_1200/996782/MNINonLinear/Results/rfMRI_REST1_RL/rfMRI_REST1_RL_Atlas_hp2000_clean.dtseries.nii"


#LR stands for Left and Right hemisphere not Left to Right scanning (as in the dtseries.nii)
atlas_file_pre  = "/MNINonLinear/fsaverage_LR32k/"
destrieux_atlas_file_post = ".aparc.a2009s.32k_fs_LR.dlabel.nii"
desikan_atlas_file_post = ".aparc.32k_fs_LR.dlabel.nii"

#paths on aws machine
path2HCP_1200 = "/hcp-openaccess/HCP_1200/"

#paths on local machine
external_hd_path = "/Volumes/Elements" #"/run/media/mwasser6/Elements"
log_file  = external_hd_path + "/download_scripts/log.txt"
local_dir = external_hd_path + "/brain_data"

#raw file location:
# /hcp-openaccess/HCP_1200/100206/MNINonLinear/Results/rfMRI_REST1_RL/rfMRI_REST1_RL_Atlas_MSMAll_hp2000_clean.dtseries.nii
############



#which files to download
# input: patient_id is a string of the patient id w/o any extra characters (e.g. '/')
def list_files(patient_id):
    patient_id = str(patient_id)

    #list of dictionaries representing each file
    files = []

    #path to directory for this suject
    subject_dir = local_dir+"/"+patient_id


    ############
    # for each file:
    # hcp_path = path to file on the aws server
    # readable_name = name to be used for printing
    # local_path = path to file on local machine
    ############

    #CHANGE: include new block (see above) for a new file.

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


    #Destrieux atlas
    hcp_path = path2HCP_1200 + patient_id + atlas_file_pre + patient_id + destrieux_atlas_file_post
    readable_name = "Destrieux_aparc32k"
    local_path = subject_dir + "/" + patient_id + destrieux_atlas_file_post
    files.append({"hcp_path": hcp_path, "readable_name": readable_name, "local_path": local_path})

    #Desikan atlas
    hcp_path = path2HCP_1200 + patient_id + atlas_file_pre + patient_id + desikan_atlas_file_post
    readable_name = "Desikan_aparc32k"
    local_path = subject_dir + "/" + patient_id + desikan_atlas_file_post
    files.append({"hcp_path": hcp_path, "readable_name": readable_name, "local_path": local_path})

    return files
#create list of string subject id's in HCP_1200. There are 1114 directories (each representing a patient)
def subject_list_HCP_1200():
    args = ["aws s3 ls s3://hcp-openaccess/HCP_1200/"]
    completed_process = subprocess.run(args, capture_output=True, shell=True)
    all_dirs = completed_process.stdout
    dir_list = str.splitlines(all_dirs.decode(encoding))
    subject_list = []

    for idx, subject in enumerate(dir_list):
        #bug in decoding? 1000th  aws call has date/time returned instead of patient_id
        if idx == 999:
            #print(f'aws returns junk on 1000th call')
            continue
        subject_id = subject.split()[1] #remove extranous stuff
        subject_id = subject_id[:-1] #remove trailing '/'
        subject_list.append(subject_id)

    return subject_list


# https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.savemat.html
def save_subject_list_to_mat():
    subject_list = subject_list_HCP_1200()
    print(f'Saving subject list of {len(subject_list)} hcp subject')
    savemat("hcp_1200_subject_list.mat", {'hcp1200_subject_list': subject_list})


#Check to see if this file exists on hcp server
def check_exist_hcp(rel_subj_path, patient_id):

    hcp_path = path2HCP_1200 + patient_id + rel_subj_path
    print(f'contructed path: {hcp_path}')
    print(f'\tChecking if  {rel_subj_path} exists ...',end='')
    args = ["aws s3 ls s3:/" + hcp_path + " " + "--human-readable"]
    completed_process = subprocess.run(args, capture_output=True, shell=True)
    out = completed_process.stdout.decode(encoding)

    #if download did not complete properly, print this and save this info
    if completed_process.returncode != 0:
        print(f'NOT EXIST...\n\t\t>> {out} ')#'ERROR (likely not on server or faulty path given')
    else:
        print(f'DOES EXIST...\n\t\t>> {out}')

patient_id = "644044"
desikan_atlas_file_post_RL = ".aparc.32k_fs_RL.dlabel.nii"
rel_hcp_path = atlas_file_pre + patient_id + desikan_atlas_file_post_RL
check_exist_hcp(rel_hcp_path, patient_id)


#for each patient, create a local diretory in local_dir and download all files. If there is an issue downloading, print to terminal and record which patient could not download each file
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

            if os.path.isfile(f['local_path']):
                print(f'\t{f["readable_name"]} already exists, skipping...')
                continue

            #if file does not already exist in local directory, attempt to download it
            print(f'\tdownloading {f["readable_name"]} into {subject_dir}...',end='')
            args = ["aws s3 cp s3:/" + f["hcp_path"] + " " + subject_dir]
            completed_process = subprocess.run(args, capture_output=True, shell=True)

            #if download did not complete properly, print this and save this info
            if completed_process.returncode != 0:
                print(f'ERROR (likely not on server or faulty path given')
                patients_missing_file[f["readable_name"]].add(subject)
            else:
                print(f'success')

        end = time.time()
        print(f"Time for download: {(end-start):.1f}")

        #Summarize whats missing: CHANGE - include new files here
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


    #End of Download Summary: CHANGE - include new files here
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
    print(f"LR: same as msmall lr? {lr_msmall_miss==lr_no_msmall_miss} \n{lr_no_msmall_miss}")
    print(f"RL: same as msmall rl? {rl_msmall_miss==rl_no_msmall_miss} \n{rl_no_msmall_miss}")
    print(f"BOTH: same as msmall both? {both_msmall_miss==both_no_msmall_miss} \n{both_no_msmall_miss}")

    print(f"\nDESIKAN missing: {patients_missing_file['Desikan_aparc32k']}")
    print(f"DESTRIE missing: {patients_missing_file['Destrieux_aparc32k']}")

    lr_no_msmall_miss = [int(a) for a in lr_no_msmall_miss]
    rl_no_msmall_miss = [int(a) for a in rl_no_msmall_miss]
    both_no_msmall_miss = [int(a) for a in both_no_msmall_miss]
    #savemat("subjects_missing_data.mat", {'missing_LR': lr_no_msmall_miss, 'missing_RL': rl_no_msmall_miss, 'missing_LR_and_RL': both_no_msmall_miss, 'type': 'no_msmall'})

#Begin download
#download_files()

#save_subject_list_to_mat()

#sl = subject_list_HCP_1200()
#print(f"999th subject_id: {sl[997:1001]}")
