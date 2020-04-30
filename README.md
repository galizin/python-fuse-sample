# python-fuse-sample-archive-transparent

I needed a file system with archive transparency, so I created this proof-of-concept update to Stavros' original script. 

What it does is when it finds a .zip or .rar file it lists it as a directory and mounts it to a special folder in the filesystem with archivemount for zip and rar2fs for rar. There is also a filter for what files it wants to hide in the virtual file system.

All settings are hardcoded.

In case you want to access or mount this filesystem remotely use sftp or sshfs. smb and nfs won't work for reasons explained here https://github.com/hasse69/rar2fs/issues/1. Reduce encryption level if needed.

Uses https://hasse69.github.io/rar2fs/ for rar mounting (installation instructions in https://github.com/hasse69/rar2fs/wiki) as archivemount doesn't work for some reason.

This is the original readme for https://github.com/skorokithakis/python-fuse-sample

# python-fuse-sample

This repo contains a very simple FUSE filesystem example in Python. It's the
code from a post I wrote a while back:

https://www.stavros.io/posts/python-fuse-filesystem/

If you see anything needing improvement or have any feedback, please open an
issue.
