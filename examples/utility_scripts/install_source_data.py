import re
import os.path
import sys
import time
import shutil
import tarfile


from sys import version_info

if version_info[0] < 3:
    # Python 2
    from urllib2 import (urlopen, Request)
    from urllib import (urlencode)
else:
    # Python 3.0 and later
    from urllib.request import (urlopen, Request)
    from urllib.parse import urlencode
    # raw_input function renamed "input" in python 3
    raw_input = input


# script to download and unpack source data for examples

source_data_dir="../source_data_2"

# fist, check to make sure it's not downloaded already

if os.path.exists(source_data_dir):
    print("\n*******")
    print("Directory: '%s'" % os.path.abspath(source_data_dir))
    print("already exists.  So, source file download download is not needed.")
    print("If you still would like to download the file, move or remove")
    print("the above directory then re-run this script.")
    sys.exit(0)


suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def humansize(nbytes):
    if nbytes == 0: return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


def confirm(prompt=None, resp=False):
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n: 
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: 
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True

    """
    if prompt is None:
        prompt = 'Confirm'
    if resp:
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')
    while True:
        ans = raw_input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print ('please enter y or n.')
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False

# From:
# http://stackoverflow.com/questions/4048651/python-function-to-convert-seconds-into-minutes-hours-and-days

def display_time(seconds, granularity=2):
    intervals = (
        ('weeks', 604800),  # 60 * 60 * 24 * 7
        ('days', 86400),    # 60 * 60 * 24
        ('hours', 3600),    # 60 * 60
        ('minutes', 60),
        ('seconds', 1),
        )
    result = []
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            # result.append("{} {}".format(value, name))
            result.append("{} {}".format(int(value), name))
    return ', '.join(result[:granularity])


# initial url is: "https://portal.nersc.gov/project/crcns/download/nwb-1"

# authentication form looks like:
#
# <body>
# <h2>CRCNS.org data download</h2>
# <form action="/project/crcns/download/index.php" method="post">
#    <input type="hidden" name="fn" value="nwb-1" />
#    <table>
#    <tr><td>username:</td><td><input type="text" name="username" /></td></tr>
#    <tr><td>password:</td><td><input type="password" name="password" /></td></tr>
#    </table>
#    <input type="submit" name="submit" value="Login" /><br /><br />
# <strong>OR</strong>,
#  Since 'nwb-1' is public, you can also access is anomyously.<br />
# 
# To login anomyously:<br />
#    <input type="hidden" name="guest" value="1" />
#    <input type="hidden" name="fn" value="nwb-1" />
#    agree to the <a href="http://crcns.org/terms">terms of use</a>:
#  <input type="checkbox" name="agree_terms"> (check to indicate you agree with the terms)<br />
#    <input type="submit" name="submit" value="Login Anonymously" /></form>
# 
# </body>

# download authentication cookie

data = {
    b"guest": b"1",
    b"fn": b"nwb-1",
    b"agree_terms": b"1",
    b"submit": b"Login Anonymously"
}

data = urlencode(data).encode('ascii')

url="https://portal.nersc.gov/project/crcns/download/index.php"


req = Request(url,
        data=data, 
        headers={b'Content-type': b'application/x-www-form-urlencoded'}) 
response = urlopen(req)

cookie = response.headers.get('Set-Cookie')

# now download file

url_dir = "https://portal.nersc.gov/project/crcns/download/nwb-1/"
filepath="example_script_data/source_data_2.tar.gz"
# filepath="hc-3/ec013.15.zip"
url2=url_dir + filepath

file_name = url2.split('/')[-1]
req2 = Request(url2)
req2.add_header('cookie', cookie)
u = urlopen(req2)

file_size = int(u.headers['Content-Length'])

# meta = u.info()
# file_size = int(meta.getheaders("Content-Length")[0])
human_size = humansize(file_size)


print ("Downloading: %s Bytes: %s (%s)" % (file_name, file_size, human_size))
proceed = confirm(prompt="Proceed?", resp=True)

if( not proceed):
    print("Download aborted.")
    sys.exit(0)



f = open(file_name, 'wb')
file_size_dl = 0
block_sz = 8192

start_time = time.time()
last_time = 0.0
delay = 3.0  # number of seconds between updating display

while True:
    buffer = u.read(block_sz)
    if not buffer:
        break
    f.write(buffer)
    file_size_dl += len(buffer)
    if time.time() - last_time > delay:
        # display update of stats
        last_time = time.time()
        elapsed_time = last_time - start_time;
        remaining_time = elapsed_time * (file_size - file_size_dl) / file_size_dl
        human_size_dl = humansize(file_size_dl)
        # add spaces at end to clear out leftover text
        status = r"%10d (%s) [%3.2f%%] (%s remaining)                   " % (file_size_dl,
             human_size_dl, file_size_dl * 100. / file_size, display_time(remaining_time))
        status = status + chr(8)*(len(status)+1)
        sys.stderr.write(status)
        sys.stderr.flush()
        # print (status,)
f.close()

print("\nDownload complete")

# unpack file

print("Extracting files from %s" % file_name)

tar = tarfile.open(file_name)
tar.extractall()
tar.close()


dir_name =re.sub('\.tar\.gz$', '', file_name)
print("Moving directory %s to %s" % (dir_name, os.path.abspath(source_data_dir)))

shutil.move(dir_name, source_data_dir)

print("Done installing %s" % os.path.abspath(source_data_dir))

print("Feel free to delete file '%s' (it is no longer needed)" % (
    os.path.abspath(file_name)))

sys.exit(0)
