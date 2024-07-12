
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y install \
    wget \
    curl \
    git \
    libssl-dev \
    python3-dev \
    python3-pip \
    python3-virtualenv \
    gsl-bin \
    libgsl-dev \
    cmake \
    swig \
    jwm \
    libglapi-mesa pkg-config libsecret-1-dev \
    libx11-dev libxkbfile-dev \
    libsecret-1-dev

THEIA_DEFAULT_PLUGINS=local-dir:/gui/theia/plugins
SHELL=/bin/bash
NODE_VERSION="20.2.0"

curl https://raw.githubusercontent.com/nvm-sh/nvm/master/nvm.sh > nvm.sh
chmod u+x nvm.sh
bash -c ". ./nvm.sh && nvm install $NODE_VERSION \
    && nvm use $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && npm install -g yarn"

export PATH=/home/ubuntu/versions/node/v${NODE_VERSION}/bin:$PATH

git clone https://github.com/vnvlabs/gui.git
cd gui
git checkout wip
git submodule update --init

cd /home/ubuntu/gui/theia
yarn --pure-lockfile
yarn theia build
cd browser-app yarn theia download:plugins --ignore-errors

cd /home/ubuntu/gui/scripts
./download_paraview.sh
mkdir paraview
tar -xf ./pv.tar.gz -C paraview --strip-components=1
rm ./pv.tar.gz

cd /home/ubuntu/gui
virtualenv virt
virt/bin/pip install -r requirements.txt

cd /home/ubuntu/gui/python_api
mkdir -p build
cd build
cmake ..
make -j


