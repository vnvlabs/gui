

ARG FROM_IMAGE=ubuntu:20.04
FROM ${FROM_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive 

ENV TZ=America/New_York


ENV THEIA_DEFAULT_PLUGINS=local-dir:/vnvgui/theia/plugins
ENV NODE_VERSION=18.12.1
ENV YARN_VERSION=1.22.5
ENV PARAVIEW_DIR=/vnvgui/paraview 
ENV PVPYTHON=${PARAVIEW_DIR}/bin/pvpython 


RUN apt-get -y update && apt-get -y upgrade && apt-get -y install \
    wget \
    curl \
    libssl-dev \
    python3-dev \
    python3-pip \
    gsl-bin \
    libgsl-dev \
    libglapi-mesa pkg-config libsecret-1-dev \
    && pip3 install virtualenv  

# Install Node.js
RUN ARCH= && dpkgArch="$(dpkg --print-architecture)" \
    && case "${dpkgArch##*-}" in \
    amd64) ARCH='x64';; \
    ppc64el) ARCH='ppc64le';; \
    s390x) ARCH='s390x';; \
    arm64) ARCH='arm64';; \
    armhf) ARCH='armv7l';; \
    i386) ARCH='x86';; \
    *) echo "unsupported architecture"; exit 1 ;; \
    esac \
    && curl -SLO "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-$ARCH.tar.xz" \
    && mkdir -p /vnvgui/node \
    && tar -xJf "node-v$NODE_VERSION-linux-$ARCH.tar.xz" -C /vnvgui/node --strip-components=1 --no-same-owner \
    && rm "node-v$NODE_VERSION-linux-$ARCH.tar.xz" \
    && ln -s /vnvgui/node/bin/node /usr/local/bin/nodejs \
    && ln -s /vnvgui/node/bin/node /usr/local/bin/node \
    &&  curl -fSLO --compressed "https://yarnpkg.com/downloads/$YARN_VERSION/yarn-v$YARN_VERSION.tar.gz" \
    && mkdir -p /opt/yarn \
    && tar -xzf yarn-v$YARN_VERSION.tar.gz -C /opt/yarn --strip-components=1 \
    && ln -s /opt/yarn/bin/yarn /usr/local/bin/yarn \
    && ln -s /opt/yarn/bin/yarn /usr/local/bin/yarnpkg \
    && rm yarn-v$YARN_VERSION.tar.gz

#Copy theia config Leave this seperate so we can cache that god awfull thing above. 
COPY docker/theia.package.json /vnvgui/theia/package.json

ENV PATH=/vnvgui/node/bin/:$PATH 

RUN cd /vnvgui/theia && mkdir plugins \
    && yarn --pure-lockfile && \
    yarn theia build && \
    yarn theia download:plugins && \
    yarn --production && \
    yarn autoclean --init && \
    echo *.ts >> .yarnclean && \
    echo *.ts.map >> .yarnclean && \
    echo *.spec.* >> .yarnclean && \
    yarn autoclean --force && \
    yarn cache clean 

#Install Pavaview server (used for visualization) 
COPY data/pv.tar.gz /data/pv.tar.gz
RUN mkdir /vnvgui/paraview
RUN tar -xf /data/pv.tar.gz -C /vnvgui/paraview --strip-components=1 && rm /data/pv.tar.gz 

#Install the vnv guo
COPY ./requirements.txt /vnvgui/gui/requirements.txt
RUN cd /vnvgui/gui \
    && virtualenv virt \
    && virt/bin/pip install -r ./requirements.txt 

COPY . /vnvgui/gui
LABEL VNV_GUI_EQUIPT=1

WORKDIR /vnvgui/gui
RUN mv docker/*.sh ./ 
ENTRYPOINT ["./launch.sh"]
