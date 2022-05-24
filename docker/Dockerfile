

ARG FROM_IMAGE=vnv_env
FROM ${FROM_IMAGE}

COPY . /vnv-gui
RUN cd /vnv-gui && virtualenv virt && virt/bin/pip install -r ./requirements.txt
COPY ./docker/launch.sh /vnv-gui/launch.sh
COPY ./docker/serve.sh /vnv-gui/serve.sh
COPY ./docker/run.sh /vnv-gui/run.sh


