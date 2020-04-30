#!/usr/bin/env python3

from __future__ import with_statement

import os
import sys
import stat
import errno
import tempfile
import subprocess

from fusepy import FUSE, FuseOSError, Operations


class Passthrough(Operations):
    def __init__(self, root):
        self.root = root
        self.archdict = {}
        if root.startswith("/"):
          rootdir = root
        else:
          rootdir = os.getcwd() + '/' +root
        self.archtemp = "/var/run/archmnt"+rootdir
        if not os.path.exists(self.archtemp):
           os.makedirs(self.archtemp)
        self.extfilter = ('.aac','.ac3','.ape','.dts','.flac','.iso','.ISO','.it','.m4a','.mid','.mod','.mp3','.Mp3','.MP3','.mpc','.nrg','.ogg','.ra','.RA','.ram','.rar','.s3m','.vgz','.wav','.WAV','.wma','.wv','.wvc','.zip')
        for i in os.listdir(self.archtemp):
             subprocess.run(['fusermount', '-u', self.archtemp+i])
             subprocess.run(['rmdir', self.archtemp+i])


    # Helpers
    # =======

    def _full_path(self, partial):
        #print('decoding path ' + partial)
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        if path in self.archdict:
           path = self.archdict[path]
        else:
          currdirname = os.path.dirname(path)
          if currdirname in self.archdict:
             if os.path.isdir(self.archdict[currdirname] + '/' + os.path.basename(path)):
                self.archdict[path] = self.archdict[currdirname] + '/' + os.path.basename(path)
             path = self.archdict[currdirname] + '/' + os.path.basename(path)
        #print('decoded into ' + path)
        return path

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        #print('accessing ' + path)
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        #print('getting attr of ' + path)
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        new_st_mode = st.st_mode
        if path.endswith((".rar", ".zip")) and not os.path.isdir(full_path):
                 new_st_mode = new_st_mode ^ 0o40000 ^ 0o100000
                 if not full_path in self.archdict:
                    foldername = tempfile.mkdtemp(dir=self.archtemp)
                    st1 = os.lstat(foldername)
                    os.chmod(foldername, st1.st_mode | 0o55)
                    self.archdict[full_path] = foldername
                    #print('added ' +full_path+ ' '+foldername)
                    if path.endswith(".rar"):
                      subprocess.run(['rar2fs', full_path, foldername])
                    else:
                      subprocess.run(['archivemount', full_path, foldername])
        if full_path in self.archdict:
          st = os.lstat(self.archdict[full_path])
          new_st_mode = st.st_mode
        attrdict = dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        attrdict['st_mode'] = new_st_mode
        return attrdict

    def readdir(self, path, fh):
        #print('reading dir ' + path)
        full_path = self._full_path(path)
        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            if r == "." or r == "..":
            	yield r
            else:
            	if os.path.isdir(full_path+"/"+r):
            		yield r
            	else:
            		if "." in r:
            			if r.endswith(self.extfilter):
            				yield r

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._full_path(path))

    def symlink(self, name, target):
        return os.symlink(name, self._full_path(target))

    def rename(self, old, new):
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        full_path = self._full_path(path)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        return os.fsync(fh)

    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)


def main(mountpoint, root):
    FUSE(Passthrough(root), mountpoint, nothreads=True, foreground=True,**{'allow_other': True})

if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])
