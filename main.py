import os

class UnsupportedOSError(Exception):
    pass

class UnsupportedFilesystemError(Exception):
    pass


def check_os_and_filesystem(path):
    if os.name != 'nt':  # Check if OS is Windows
        raise UnsupportedOSError("This function can only run on Windows.")

    # Check if the target path is on NTFS filesystem
    import subprocess
    result = subprocess.run(['fsutil', 'fsinfo', 'volumeinfo', path], capture_output=True, text=True)
    if 'NTFS' not in result.stdout:
        raise UnsupportedFilesystemError("The specified path is not on NTFS filesystem.")

    return True
