# DVDRawBruteforce
Bruteforces various 0x3C and 0xF1 SCSI parameters (as well as checking for 0xE7, 0x3E, and 0x9E) to expose parts of the cache that might potentially store raw DVD sector data.

It determines this data by storing LBA 0 onto the cache and by bruteforcing various known commands that expose the cache in order to find the data that's stored.
Data from LBA 0 should always start with "00 03 00 00" as the first 4 bytes of the sector. This denotes the PSN of 30000.

Script has been written for use with Windows 10 x64 and Python 3.11.4.

Hidden-Palace R&D
