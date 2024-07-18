

ARG FROM_IMAGE=ubuntu:20.04
FROM ${FROM_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/New_York

ENV PATH=/node/bin/:$PATH


RUN apt-get -y update && apt-get -y upgrade && apt-get -y install \
    wget \
    curl \
    git \
    libssl-dev \
    python3-dev \
    python3-pip \
    python3-virtualenv \
    gsl-bin \
    libgsl-dev \
    swig \
    jwm \
    libglapi-mesa pkg-config libsecret-1-dev \
    libx11-dev libxkbfile-dev \
    libsecret-1-dev

ENV THEIA_DEFAULT_PLUGINS=local-dir:/gui/theia/plugins
ENV SHELL=/bin/bash
ENV NODE_VERSION="20.2.0"
RUN curl https://raw.githubusercontent.com/nvm-sh/nvm/master/nvm.sh > nvm.sh
RUN chmod u+x nvm.sh
RUN bash -c ". ./nvm.sh && nvm install $NODE_VERSION \
    && nvm use $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && npm install -g yarn"

ENV PATH=/versions/node/v${NODE_VERSION}/bin:$PATH

RUN echo "force"
RUN git clone https://github.com/vnvlabs/gui.git && cd gui && git checkout wip
RUN cd gui/theia && yarn --pure-lockfile && yarn theia build && cd browser-app && yarn theia download:plugins --ignore-errors
RUN cd gui/scripts && ./download_paraview.sh && mkdir paraview && tar -xf ./pv.tar.gz -C paraview --strip-components=1 && rm ./pv.tar.gz

RUN echo "force"
RUN cd gui && git pull
RUN cd gui && virtualenv virt && virt/bin/pip install -r requirements.txt
RUN cd gui && git submodule update --init
RUN cd gui/python_api && mkdir -p build && cd build && cmake .. && make -j

RUN apt-get install -y vim
RUN echo "sdfsf" && cd gui && git pull
ENV PARAVIEW_DIR=/gui/scripts/paraview
ENV PVPYTHON=${PARAVIEW_DIR}/bin/pvpython

RUN echo "sdfo3sdf3fsdfsi55sdfsdsdfr4354f"



RUN cd gui && git pull

WORKDIR ./gui
ENTRYPOINT ["/gui/virt/bin/python","run.py","--profile","docker"]
CMD ["--address", "0.0.0.0"]
