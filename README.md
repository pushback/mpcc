# mpcc
mpcc stands for mpc client.<br>
MPD is controlled by mpc and supports folder-based music playback at web browser.

![](https://user-images.githubusercontent.com/1241251/65836691-c08c5800-e32c-11e9-844d-422b829c56e6.png)

## Install

Require python3, mutagen(MP3 tag liblary for coverart display), MPD(playing mp3), mpc(controll MPD).

Run install.sh and reboot your Linux machine.

install.sh performs the following operations:

* Install mutagen by "pip install" if needed.
* Install MPD and mpc by "apt install" if needed.
* Copy mpcc.py to /opt/mpcc
* Regist mpcc.service by systemctl.

~~~
$ git clone https://github.com/pushback/mpcc.git
$ cd mpcc
$ ./install.sh
~~~

## Usage

* Copy MP3 file to "/media/music"
* Edit "/etc/mpd.cfg", music_directory to "/media/music".
* Open web browser http://localhost or IP Address of server(from other machine or phone).
* At first time, you must click two button("DB Update" -> "Init Queue").
* Select file at folder/file list

## Help
* "<<" button : play previous file.
* "|>" button : toggle play/pause.
* ">>" button : play next file.
* "V-" button : Volume Down.
* "V+" button : Volume Up.
* "Playing dir" button : move directory to now playing file exists.
* "Init Queue" button : (add all music file to play queue for folder based playing).
* "DB Update" button : music file rescan

## Modify and restart

~~~
# modify
sudo vim /opt/mpcc/mpcc.py

# restart
sudo systemctl restart mpcc
~~~

## Mechanism

This program execute "mpc xxx" for controll MPD.
For example,
* Play next file is "mpc next"
* Play select file is "mpc searchplay filename \[select file path\]"

## Background
I wrote this program for small music player used Raspberry Pi.<br>
I wanted to control the player with a desktop computer or smartphone.
