

ARG FROM_IMAGE=vnv_env
FROM ${FROM_IMAGE}

#Install Pavaview server (used for visualization) 
RUN mkdir /vnv-gui
RUN wget -O pv.tar.gz "https://www.paraview.org/paraview-downloads/download.php?submit=Download&version=v5.10&type=binary&os=Linux&downloadFile=ParaView-5.10.1-osmesa-MPI-Linux-Python3.9-x86_64.tar.gz"   
RUN tar -xf pv.tar.gz && mv ParaView-5.10.1-osmesa-MPI-Linux-Python3.9-x86_64 /vnv-gui/paraview && rm pv.tar.gz 

COPY . /vnv-gui

RUN cd /vnv-gui \
    && virtualenv virt \
    && virt/bin/pip install -r ./requirements.txt \
    && mv docker/*.sh ./ 


ENV PARAVIEW_DIR=/vnv-gui/paraview 
ENV PVPYTHON=${PARAVIEW_DIR}/bin/pvpython 

#Install vim for text editing. and gdb TODO move these to the env image
RUN apt-get install -y vim gdb 

WORKDIR /vnv-gui
ENTRYPOINT ["./launch.sh"]
