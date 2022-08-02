

ARG FROM_IMAGE=vnv_env
FROM ${FROM_IMAGE}

COPY . /vnv-gui

RUN cd /vnv-gui \
    && virtualenv virt \
    && virt/bin/pip install -r ./requirements.txt \
    && mv docker/*.sh ./ 


