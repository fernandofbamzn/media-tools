# Project Context

Project: media-tools

media-tools is a CLI application designed to manage and analyze multimedia libraries.

Primary goals:

- inspect MKV/MP4 media files
- analyze audio and subtitle tracks
- remove duplicated tracks
- keep only selected languages
- generate reports about media libraries
- optionally optimize media files

Typical environment:

Linux server  
Proxmox LXC containers  
large media libraries mounted via NFS or bind mounts

Primary tools used by the application:

mkvmerge  
ffmpeg  
mediainfo  

Python stack:

Typer  
Rich  
Questionary  

Architecture:

CLI → Services → Repository → Models

The application must remain safe for large media libraries and must never modify files without explicit user confirmation.

