# ----------------------------------------
# install mpcc
# ----------------------------------------

# mutagen install
sudo pip install mutagen

# MPD, mpc install
sudo apt install mpd mpc

# Script install
sudo mkdir /opt/mpcc/
sudo cp ./mpcc.py /opt/mpcc

# Register systemd service
sudo cp ./mpcc.service /etc/systemd/system/
sudo systemd enable mpcc

# quit message
echo "reboot for start mpcc."

