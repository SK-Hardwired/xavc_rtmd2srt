# XAVC RTMD -> SRT
Extract real time meta-data from Sony XAVC video and render to srt subtitle file

Besides of non-realtime metadata which MediaInfo or Exiftool can see, Sony cameras record many other real-time meta-data for every frame such as it's ISO, F number, shutter speed, AE mode and even focus distance.

This tool tries to extract these from XAVC S (MP4) file and create SRT subtitle file near the video file. When opened in VLC or whatever, it can be viewed and you can see the settings of camera for every frame of video in real time.

Windows x64 executable available (see zip file in files list). Usage: as any console app, accepts 1 argument (full video file path or just file name if in the same folder)
Example: **xavcs_rtmd_bin_2.exe D:\Video\C0035.MP4**

Note: Works well with Sony ILCE-9/7RM3/7M3, DSC-RX10M4 and FDR-AX700 videos. Limited compatibility with ActionCam videos - works well if no GPS data captured.
