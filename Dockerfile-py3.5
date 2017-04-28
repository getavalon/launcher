FROM ubuntu:16.04

RUN apt-get update && \
    apt-get install -y \
        nano \
        wget \
        git \
        python3 \
        python3-pyqt5 \
        xvfb

RUN wget https://bootstrap.pypa.io/get-pip.py && \
	python3 get-pip.py && \
	python3 -m pip install \
		nose \
		nose-exclude \
		coverage \
		PyQt5

# Xvfb
ENV DISPLAY :99

WORKDIR /workspace/launcher

ENTRYPOINT cp -r /launcher /workspace && \
    Xvfb :99 -screen 0 1024x768x16 2>/dev/null & \
    while ! ps aux | grep -q '[0]:00 Xvfb :99 -screen 0 1024x768x16'; \
        do echo "Waiting for Xvfb..."; sleep 1; done && \
    echo "#\n# Testing implementation.." && \
        python3 -u run_tests.py && \
    echo Done
