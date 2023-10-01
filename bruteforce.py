# Raw DVD Drive sector reading Bruteforcer
# Version: 2023-09-30
# Author: ehw
# Hidden-Palace.org R&D
# Description: Bruteforces various 0x3C and 0xF1 SCSI parameters (as well as checking for 0xE7, 0x3E, and 0x9E) to expose parts of the cache that might potentially store raw DVD sector data. 
#              It determines this data by storing LBA 0 onto the cache and by bruteforcing various known commands that expose the cache in order to find the data that's stored.
#              Data from LBA 0 should always start with "00 03 00 00" as the first 4 bytes of the sector. This denotes the PSN of 30000.
# Notes: Script has been written for use with Windows 10 x64 and Python 3.11.4.

import subprocess
import win32api
import win32com.client
import sys
import os
import shutil
from datetime import datetime
import zipfile
import time
import glob
from tqdm import tqdm
    
class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("logfile.log", "a")
   
    def write(self, message):
        self.terminal.write(message)
        if not self.log.closed:
          self.log.write(message)  

    def flush(self):
        pass    

sys.stdout = Logger()

def zip_files():
    zip_filename = "upload_me.zip"
    files_to_zip = glob.glob("*.bin") + ["logfile.log"]
    
    with zipfile.ZipFile(zip_filename, "w") as zip_file:
        for file in files_to_zip:
            zip_file.write(file)
    
    print(f"Files zipped successfully into '{zip_filename}'. Please send this zip file for analysis.")

def execute_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    return process.returncode, output.decode('utf-8').strip(), error.decode('utf-8').strip()

def dvd_drive_exists(drive_letter):
    drive_path = drive_letter + ':\\'
    return os.path.isdir(drive_path)

def read_lba_0(drive_letter):
    print("Reading LBA 0 to store on the cache")
    command = f"sg_raw.exe -r 2048 {drive_letter}: a8 00 00 00 00 00 00 00 00 01 00 00"
    execute_command(command)

def scan_for_3c_values(drive_letter):
    print("\nScanning for 3C values (THIS MAY TAKE A WHILE)...")
    discovered_files = []
    total_iterations = 256 * 256
    progress_bar = tqdm(total=total_iterations, desc="Processing")

    for xx in range(256):
        for yy in range(256):
            command = f"sg_raw.exe -o 3c_{xx:02X}_{yy:02X}.bin -r 2384 {drive_letter}: 3c {xx:02X} {yy:02X} 00 00 00 00 09 50 00"
            return_code, _, _ = execute_command(command)

            filename = f"3c_{xx:02X}_{yy:02X}.bin"
            try:
             with open(filename, "rb") as file:
                 first_four_bytes = file.read(4)
             if first_four_bytes == b"\x00\x03\x00\x00":
                 print(f"\nRaw sector data found with 3C {xx:02X} {yy:02X}")
                 discovered_files.append(filename)
                 command = f"sg_raw.exe -o 3c_{xx:02X}_{yy:02X}_(16128).bin -r 16128 {drive_letter}: 3c {xx:02X} {yy:02X} 00 00 00 00 3F 00 00" #make a 16kb dump for further analysis
                 return_code, _, _ = execute_command(command)
             else:
                 print(f"\nRaw sector data NOT found with 3C {xx:02X} {yy:02X}")
            except FileNotFoundError:
             pass
             
            # Update the progress bar
            progress_bar.update(1)
            
    # Close the progress bar
    progress_bar.close()
    return discovered_files

def scan_for_f1_values(drive_letter):
    print("\nScanning for F1 values (THIS MAY TAKE A WHILE)...")
    discovered_files = []
    total_iterations = 256 * 256
    progress_bar = tqdm(total=total_iterations, desc="Processing")

    for xx in range(256):
        command = f"sg_raw.exe -o f1_{xx:02X}.bin -r 2384 {drive_letter}: f1 {xx:02X} 00 00 00 00 00 00 09 50"
        return_code, _, _ = execute_command(command)

        filename = f"f1_{xx:02X}.bin"
        try:
         with open(filename, "rb") as file:
             first_four_bytes = file.read(4)
         if first_four_bytes == b"\x00\x03\x00\x00":
             print(f"\nRaw sector data found with F1 {xx:02X}")
             command = f"sg_raw.exe -o f1_{xx:02X}_(16128).bin -r 16128 {drive_letter}: f1 {xx:02X} 00 00 00 00 00 00 3F 00" #make a 16kb dump for further analysis
             return_code, _, _ = execute_command(command)
             discovered_files.append(filename)
         else:
            print(f"\nRaw sector data NOT found with F1 {xx:02X}")
        except FileNotFoundError:
         pass
        
        # Update the progress bar
        progress_bar.update(1)
        
    # Close the progress bar
    progress_bar.close()
    return discovered_files

def test_e7_command(drive_letter):
    print("\nTesting if E7 SCSI command (Hitachi Debug - Type 3/4 NO OFFSET) is supported...")
    command = f"sg_raw.exe -o e7.bin -r 2064 {drive_letter}: e7 48 49 54 01 00 80 00 00 00 80 10"
    return_code, _, _ = execute_command(command)
    try:
     with open("e7.bin", "rb") as file:
         first_four_bytes = file.read(4)
     if first_four_bytes == b"\x00\x03\x00\x00":
         print("Raw sector data found with E7 (Hitachi Debug)")
     else:
         print("Raw sector data NOT found but a file was generated with the E7 SCSI command (Hitachi Debug)")
    except FileNotFoundError:
         print("E7 SCSI Command (Hitachi Debug) NOT supported.")
         pass

def test_3e_read_long_10(drive_letter):
    print("\nTesting if 3E SCSI Command (READ LONG (10)) is supported...")
    # xfer_len=2384 (0x950), lba=0 (0x0), correct=0 (dont correct ecc)
    command = f"sg_raw.exe -o 3e.bin -r 2384 {drive_letter}: 3e 00 00 00 00 00 00 09 50 00"
    return_code, _, _ = execute_command(command)
    try:
     with open("3e.bin", "rb") as file:
         first_four_bytes = file.read(4)
     if first_four_bytes == b"\x00\x03\x00\x00":
         print("Raw sector data found with 3E SCSI Command (READ LONG (10)).")         
     else:
         print("Raw sector data NOT found but a file was generated with the 9E SCSI Command (READ LONG (10)).")
    except FileNotFoundError:
         print("3E SCSI Command (READ LONG (10)) NOT supported")
         pass

def test_9e_read_long_16(drive_letter):
    print("\nTesting if 9E SCSI Command (READ LONG (16)) is supported...")
    # xfer_len=2384 (0x950), lba=0 (0x0), correct=0 (dont correct ecc)
    command = f"sg_raw.exe -o 9e.bin -r 2384 {drive_letter}: 9e 11 00 00 00 00 00 00 00 00 00 00 09 50 00 00"
    return_code, _, _ = execute_command(command)
    try:
     with open("9e.bin", "rb") as file:
         first_four_bytes = file.read(4)

     if first_four_bytes == b"\x00\x03\x00\x00":
         print("Raw sector data found with 9E SCSI Command (READ LONG (16)).")
     else:
         print("Raw sector data NOT found but a file was generated with the 9E SCSI Command (READ LONG (16)).")
    except FileNotFoundError:
         print("9E SCSI Command (READ LONG (16)) NOT supported.")
         pass

def get_dvd_drive_info(drive_letter):
    wmi = win32com.client.GetObject("winmgmts:")

    # Query the Win32_CDROMDrive class for the specified drive letter
    drives = wmi.ExecQuery(f"SELECT * FROM Win32_CDROMDrive WHERE Drive = '{drive_letter}:'")

    for drive in drives:
        # Retrieve all properties of the DVD drive
        properties = drive.Properties_
        property_names = [prop.Name for prop in properties]
        property_values = drive.Properties_

        # Print the retrieved information
        print(f"\n\n--- DVD Drive Information ({drive_letter}:) ---")

        for name, value in zip(property_names, property_values):
            print(f"{name}: {value}")

        print("--------------------------------------------\n")

def get_mode_sense_page01(drive_letter):
    # Step 1: Execute sg_raw.exe command
    command = f'sg_raw.exe -o 5a_mode_sense_page01.bin -r 16 {drive_letter}: 5A 00 01 00 00 00 00 00 0F 00'
    subprocess.run(command, shell=True)

    # Step 2: Open and read the binary file
    with open('5a_mode_sense_page01.bin', 'rb') as file:
        data = file.read()

    # Step 3: Print mode sense page header
    print("------------ MODE SENSE (10) - READ-WRITE ERROR RECOVERY PAGE SETTINGS ------------")

    # Step 4: Check the value at offset 0x8
    offset_8_value = data[0x8]
    if offset_8_value == 0x01:
        print("Page Setting: READ-WRITE ERROR RECOVERY")

    # Step 5: Print the page size
    page_size = data[0x9]
    print("Page Size:", page_size, "bytes")

    # Step 6: Print flags
    print("Flags:")

    # Step 7: Print each bit from the byte at offset 0xB
    flags_byte = data[0xA]
    flag_names = [
        "AWRE (AUTOMATIC WRITE REALLOCATION ENABLE)",
        "ARRE (AUTOMATIC READ REALLOCATION ENABLE)",
        "TB (TRANSFER BLOCK)",
        "RC (READ CONTINUOUS)",
        "EER (EARLY RECOVERY)",
        "PER (POST ERROR RECOVERY)",
        "DTE (DISABLE TRANSFER on ERROR)",
        "DCR (DISABLE CORRECTION)"
    ]
    for i, flag_name in enumerate(flag_names, start=1):
        bit_value = (flags_byte >> (8 - i)) & 0x01
        print(f"\t{i}. {flag_name}: {bit_value}")

    # Step 8: Print READ RETRY COUNT
    read_retry_count = data[0xB]
    print("READ RETRY COUNT:", hex(read_retry_count))

    # Step 9: Print CORRECTION SPAN
    correction_span = data[0xC]
    print("CORRECTION SPAN:", hex(correction_span))

    # Step 10: Print HEAD OFFSET COUNT
    head_offset_count = data[0xD]
    print("HEAD OFFSET COUNT:", hex(head_offset_count))

    # Step 11: Print RESERVED (NOT USED)
    reserved_value = data[0xE]
    print("RESERVED (NOT USED):", hex(reserved_value))
    print("-----------------------------------------------------------------------------------")
    return 0

def create_new_directory():
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d %H.%M.%S")
    new_dir = os.path.join(os.getcwd(), date_time)
    
    os.makedirs(new_dir)
    print(f"\nCreated directory: {new_dir}. The .bin dumps, log file, and upload_me.zip will be found there.")
    
    return new_dir

def calc_sector_size(file_path):
    pattern_start = bytes.fromhex("00 03 00 00")
    pattern_end = bytes.fromhex("00 03 00 01")
    
    with open(file_path, "rb") as file:
        file_content = file.read()
        
        start_index = file_content.find(pattern_start)
        end_index = file_content.find(pattern_end, start_index)
        
        if start_index != -1 and end_index != -1:
            bytes_found = end_index - start_index + len(pattern_end) - 4
            return bytes_found
    
    return 0

def main():
    start_time = time.time()
    # Start
    print("Raw DVD Drive sector reading Bruteforcer")
    print("Version: 2023-06-17")
    print("Author: ehw (Hidden-Palace.org R&D)")
    print("Description: Bruteforces various 0x3C and 0xF1 SCSI parameters (as well as checking for 0xE7, 0x3E, and 0x9E) to expose parts of the cache that might potentially store raw DVD sector data. It determines this data by storing LBA 0 onto the cache and by bruteforcing various known commands that expose the cache in order to find the data that's stored. Data from LBA 0 should always start with '00 03 00 00' as the first 4 bytes of the sector. This denotes the PSN of 30000.\n") 

    # Ask the user for the drive letter of the DVD drive they want to read from.
    print("Enter the drive letter of your DVD drive: ")
    drive_letter = input()
    
    # Check if the drive the user specified actually exists.
    if dvd_drive_exists(drive_letter):
        print(f"A DVD drive exists at drive letter {drive_letter}.")
    else:
        print(f"No DVD drive found at drive letter {drive_letter}.")
        exit

    # Call the function to retrieve DVD drive information
    get_dvd_drive_info(drive_letter.upper())

    # Call function to return page 01 from mode sense. This will help determine default settings set on the drive.
    print("Checking MODE SENSE PAGE 01 (READ-WRITE ERROR RECOVERY) settings...:\n")
    get_mode_sense_page01(drive_letter)

    # Load LBA 0 (PSN 30000)'s data onto the cache. Some drives might load blocks of 16 sectors starting with an easily divisible sector.
    read_lba_0(drive_letter)
    
    # Start scanning and discovering SCSI opcodes that work.
    discovered_3c_files = scan_for_3c_values(drive_letter)
    discovered_f1_files = scan_for_f1_values(drive_letter)

    # Return the results of the bruteforcing.
    print("Possible commands that may be able to dump raw sector data:\n")
    print("3C (XX YY) - READ BUFFER")
    print("\n".join(discovered_3c_files))
    print("\n")
    print("F1 (XX)    - DEBUG COMMAND (Mediatek only?)")
    print("\n".join(discovered_f1_files))

    # Todo: E7 command support
    test_e7_command(drive_letter)
    
    # Todo: 3E command support
    test_3e_read_long_10(drive_letter)
    
    # Todo: 9E command support
    test_9e_read_long_16(drive_letter)

    # TESTING: Calculate the possible sector size returned by the drive by returning the distance between the byte pattern 00 03 00 00 (PSN $30000, or the first LBA (0)) and byte pattern 00 03 00 01 (PSN $30001, or the second LBA (1)).
    #           Do this on just the .bin files on the directory that have (16128) in the filename, as those will contain data for multiple raw sectors.
    file_extension = ".bin"
    keyword = "(16128)"
    
    current_directory = os.getcwd()
    file_list = os.listdir(current_directory)
    
    matching_files = [file for file in file_list if file.endswith(file_extension) and keyword in file]
    
    for file in matching_files:
        file_path = os.path.join(current_directory, file)
        bytes_found = calc_sector_size(file_path)
        print(f" File (SCSI Command): {file}\nPossible sector size: {bytes_found}\n")

    # End
    print("\nScript finished!\n")
    # Call the function to create the zip file
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Print script duration.
    print(f"Elapsed time: {elapsed_time} seconds")
    sys.stdout.log.close()
    
    print(f"Zipping files, this might take a while...")
    # Zip the files for submission.
    zip_files()
    
    # Move all the .bin files to a folder named after the current time, this will prevent users from accidentally running the script again and mixing the files up in different runs from different drives.
    current_dir = os.getcwd()
    new_dir = create_new_directory()
    files_to_move = [".bin", "logfile.log", "upload_me.zip"]

    for file in os.listdir(current_dir):
        if file.endswith(tuple(files_to_move)) and os.path.isfile(file):
            source_path = os.path.join(current_dir, file)
            destination_path = os.path.join(new_dir, file)
            shutil.move(source_path, destination_path)
    
    # Pause the program for user confirmation and review.
    os.system("pause")
    
if __name__ == "__main__":
    main()
