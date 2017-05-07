sudo apt-get -y update
sudo apt-get -y upgrade
#sudo rpi-update

### INSTALL OPENCV ####
sudo apt-get install -y git

### INSTALL OPENCV ####
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
#sudo pip install virtualenv virtualenvwrapper


sudo rm -rf ~/.cache/pip
sudo apt-get install -y python2.7-dev

#sudo pip install numpy

#wget -O opencv-2.4.10.zip http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.10/opencv-2.4.10.zip/download
#unzip opencv-2.4.10.zip
#cd opencv-2.4.10
#mkdir build
#cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local -D BUILD_NEW_PYTHON_SUPPORT=ON -D INSTALL_C_EXAMPLES=ON -D INSTALL_PYTHON_EXAMPLES=ON  -D BUILD_EXAMPLES=ON .
#make
#sudo make install
#sudo ldconfig


sudo apt-get install -y python-numpy
sudo apt-get install -y python-scipy
sudo apt-get install -y python-opencv
sudo apt-get install -y ipython
sudo ldconfig

#wget -O opencv-2.4.10.zip http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.10/opencv-2.4.10.zip/download
#unzip opencv-2.4.10.zip
#cd opencv-2.4.10

#mkdir build
#cd build
#cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local -D BUILD_NEW_PYTHON_SUPPORT=ON -D INSTALL_C_EXAMPLES=ON -D INSTALL_PYTHON_EXAMPLES=ON  -D BUILD_EXAMPLES=ON ..
#make
#sudo make install
#sudo ldconfig

### INSTALL OPENCV ####
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

