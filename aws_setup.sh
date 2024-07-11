sudo apt-get update -y
sudo apt-get upgrade -y

sudo apt-get install -y wget curl git libssl-dev python3-dev python3-pip
sudo apt-get install -y gsl-bin libgsl-dev cmake swig libglapi-mesa pkg-config libsecret-1-dev
sudo apt-get -y install python3-virtualenv

#Clone the gui
git clone https://github.com/vnvlabs/gui.git

# Download parview.
./gui/download_paraview.sh
tar -xf pv.tar.gz




#Download and install NODE
export NODE_VERSION=22.0.0
export YARN_VERSION=1.22.19

ARCH= && dpkgArch="$(dpkg --print-architecture)" \
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
    && mkdir -p ~/node \
    && tar -xJf "node-v$NODE_VERSION-linux-$ARCH.tar.xz" -C ~/node --strip-components=1 --no-same-owner \
    && rm "node-v$NODE_VERSION-linux-$ARCH.tar.xz" \
    && sudo ln -s ~/node/bin/node /usr/local/bin/nodejs \
    && sudo ln -s ~/node/bin/node /usr/local/bin/node \
    &&  curl -fSLO --compressed "https://yarnpkg.com/downloads/$YARN_VERSION/yarn-v$YARN_VERSION.tar.gz" \
    && mkdir -p ~/yarn \
    && tar -xzf yarn-v$YARN_VERSION.tar.gz -C ~/yarn --strip-components=1 \
    && sudo ln -s ~/yarn/bin/yarn /usr/local/bin/yarn \
    && sudo ln -s ~/yarn/bin/yarn /usr/local/bin/yarnpkg \
    && rm yarn-v$YARN_VERSION.tar.gz

cd ~/gui/theia
yarn --pure-lockfile && cd browser-app && yarn theia download:plugins --ignore-errors
