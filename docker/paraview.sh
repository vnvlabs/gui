#!/bin/bash 

# Launch with mapping Theia and Paraview. This is used by the serve app
echo "Installing Paraview Dependencies" > $1

apt-get -y install wget curl git libglapi-mesa  

if [[ x"${DOWNLOAD_PARAVIEW}" == "x1"  ]]; then


mkdir /vnvgui/paraview
echo "Downloading the Paraview Source code" > $1
wget -O pv.tar.gz "https://www.paraview.org/paraview-downloads/download.php?submit=Download&version=v5.10&type=binary&os=Linux&downloadFile=ParaView-5.10.1-osmesa-MPI-Linux-Python3.9-x86_64.tar.gz"  >> $1
echo "Installing the Paraview Source code" > /vnvgui/paraview/.vnvstatus >> $1
tar -xf pv.tar.gz -C /vnvgui/paraview --strip-components=1  >> $1
echo "Cleaning up" > /vnvgui/paraview/.vnvstatus  >> $1
rm pv.tar.gz  >> $1

fi

rm $1

# Start the paraview visualizer server
cd /vnvgui/paraview
bin/pvpython -m paraview.apps.visualizer --host $2 --data / --port $3 --timeout 600000 &


