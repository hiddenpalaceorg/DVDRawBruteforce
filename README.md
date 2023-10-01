# DVDRawBruteforce
Bruteforces various 0x3C and 0xF1 SCSI parameters (as well as checking for 0xE7, 0x3E, and 0x9E) to expose parts of the cache that might potentially store raw DVD sector data.

It determines this data by storing LBA 0 onto the cache and by bruteforcing various known commands that expose the cache in order to find the data that's stored.
Data from LBA 0 should always start with "00 03 00 00" as the first 4 bytes of the sector. This denotes the PSN of 30000.

Script has been written for use with Windows 10 x64 and Python 3.11.4. Requires sg_raw.exe (from sg3_utils) and Cygwin (cygsgutils2-1-47-2.dll and cygwin1.dll) to use.

See the latest database of checked drives here:
https://docs.google.com/spreadsheets/d/1pu3oXHRJ_qlyXrsHUyXOzD5mNp7dU8rgrfVuRBLyQFA/edit?pli=1#gid=0

For submissions, feel free to e-mail the upload_me.zip to hp@hiddenpalace.org. If the .zip is too large, upload it to a 3rd party website like MediaFire or MEGA.

Hidden-Palace R&D
