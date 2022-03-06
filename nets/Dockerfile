FROM python:3.7.9-buster
 
LABEL maintainer="danny.diaz@utexas.edu"

SHELL ["/bin/bash", "-c"]

WORKDIR /mutcompute_2020/mutcompute


# This has been modified so it works from the mutcompute2.0 repo. 
COPY mutcompute/dependencies 	dependencies
COPY mutcompute/src 		    src
COPY mutcompute/scripts         scripts
COPY mutcompute/model           model
# Overwrites default dependences to add api dependencies on top of net dependencies
COPY requirements.txt           dependencies/requirements.txt

RUN pip install -r dependencies/requirements.txt && \
    cd src/box_builder && python setup.py --verbose build_ext --inplace

WORKDIR /mutcompute_2020/mutcompute/dependencies/freesasa-2.0.3
RUN autoreconf -i && ./configure --disable-xml --disable-json && make && make install

ENV PYTHONPATH /mutcompute_2020/api:/mutcompute_2020/mutcompute:/mutcompute_2020

COPY api /mutcompute_2020/api

WORKDIR /mutcompute_2020/api

ENTRYPOINT ["bash"]
