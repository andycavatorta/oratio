echo
echo "RASPBIAN UPDATES"
echo

sudo apt-get -y update
sudo apt-get -y upgrade

echo
echo "INSTALL GIT AND PULL REPOS"
echo

sudo apt-get install -y git

git config --global user.name andycavatorta
git config --global user.email andycavatorta@gmail.com
git config --global color.ui auto


git clone https://github.com/andycavatorta/thirtybirds-2.0.git
cd thirtybirds-2.0
git remote add upstream https://github.com/andycavatorta/thirtybirds-2.0.git
cd ..
git clone https://github.com/andycavatorta/oratio.git
cd oratio
git remote add upstream https://github.com/andycavatorta/oratio.git
cd ..

echo
echo "COPY NEW RC.LOCAL FILE"
echo

sudo cp /home/pi/scripts/rc.local /etc/rc.local

#sudo ssh-keygen
#echo 
#echo "copy the key below to github /setting/deploy keys for the oratio repo"
#echo 
#sudo more /root/.ssh/id_rsa.pub

echo
echo "INSTALL OPENCV AND REQUIREMENTS"
echo

sudo apt-get install -y cmake
sudo apt-get install -y libjpeg8-dev
sudo apt-get install -y libtiff5-dev
sudo apt-get install -y libjasper-dev 
sudo apt-get install -y libgtk2.0-dev
sudo apt-get install -y libavcodec-dev
sudo apt-get install -y libavformat-dev
sudo apt-get install -y libswscale-dev
sudo apt-get install -y libv4l-dev
sudo apt-get install -y libatlas-base-dev gfortran
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py

sudo rm -rf ~/.cache/pip
sudo apt-get install -y python2.7-dev

sudo apt-get install -y python-numpy
sudo apt-get install -y python-scipy
sudo apt-get install -y python-opencv
sudo apt-get install -y ipython
sudo ldconfig

echo
echo "INSTALL THIRTYBIRDS REQUIREMENTS"
echo

sudo apt-get install -y python-netifaces
sudo apt-get install -y python-yaml
sudo apt-get install -y libtool pkg-config build-essential autoconf automake
wget https://github.com/jedisct1/libsodium/releases/download/1.0.3/libsodium-1.0.3.tar.gz
tar -zxvf libsodium-1.0.3.tar.gz
cd libsodium-1.0.3/
./configure
make
sudo make install
cd ..
wget http://download.zeromq.org/zeromq-4.1.3.tar.gz
tar -zxvf zeromq-4.1.3.tar.gz
cd zeromq-4.1.3/
./configure
make
sudo make install
sudo ldconfig
sudo pip install pyzmq

echo
echo "INSTALL THIRTYBIRDS REQUIREMENTS"
echo