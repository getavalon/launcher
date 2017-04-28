FROM mottosso/docker-qt:py2.7

WORKDIR /workspace/launcher

ENTRYPOINT cp -r /launcher /workspace && \
    Xvfb :99 -screen 0 1024x768x16 2>/dev/null & \
    while ! ps aux | grep -q '[0]:00 Xvfb :99 -screen 0 1024x768x16'; \
        do echo "Waiting for Xvfb..."; sleep 1; done && \
    echo "#\n# Testing implementation.." && \
        python -u run_tests.py && \
    echo Done
