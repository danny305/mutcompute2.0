FROM ubuntu:20.04 as builder

# This dockerfile is just for the cif pipeline.
# The pdb pipeline is deprecated and requires the dependencies/pdb2pqr2.1 and python2 and 3

WORKDIR /dependencies

ENV TZ=US/Central
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update --fix-missing && \
    apt-get install -y \
        git build-essential cmake ninja-build vim wget curl rsync autotools-dev \
        lsb-release software-properties-common libomp-dev yasm libffi-dev \
        libgtest-dev libeigen3-dev libboost-all-dev \
        libfmt-dev nlohmann-json3-dev python3-pybind11 \
        python3-dev python3-pip clang libc++-dev libc++abi-dev unzip libblas-dev liblapack-dev

# Install ChimeraX
# Download the .deb from https://www.rbvi.ucsf.edu/chimerax/download.html
# place it in the dependencies directory.
COPY dependencies /dependencies
RUN apt-get install -y /dependencies/chimerax-daily.deb && \
    mkdir -p /non/existent/directory/.local/share/ChimeraX && rm /dependencies/chimerax-daily.deb

# Install ChargeFW2
RUN git clone https://github.com/jlblancoc/nanoflann.git && \
    cd nanoflann && mkdir build && cd build && \
    cmake .. -DCMAKE_CXX_COMPILER=g++ && \
    make && make install

RUN git clone https://github.com/project-gemmi/gemmi.git && \
    cp -r gemmi/include/gemmi /usr/include

RUN git clone https://github.com/danny305/ChargeFW2.git && \
    cd ChargeFW2 && git checkout patch/cutoff-limits && mkdir build && cd build && \
    cmake .. -GNinja \
        -DCMAKE_CXX_COMPILER=clang++ \
        -DCMAKE_BUILD_TYPE=Release && \
    ninja && ninja install

# Add ChargeFW2 to the PYTHONPATH and keep it on a single thread
ENV PYTHONPATH=/usr/local/lib
ENV OMP_NUM_THREADS=1

# Install FreeSASA
RUN git clone https://github.com/danny305/freesasa.git && \
    cd freesasa && git checkout master && git submodule update --init && \
    autoreconf -i && ./configure --disable-xml --disable-json CC=clang CXX=clang++ && \
    make && make install

WORKDIR /apchem

RUN unzip /dependencies/ApChem-master.zip && rm /dependencies/ApChem-master.zip && mv ./ApChem-master ApChem && pip install ./ApChem && \
    pip3 install /dependencies/ApBio/$(ls /dependencies/ApBio) && \
    unzip /dependencies/Negatron-master.zip && rm /dependencies/Negatron-master.zip && mv ./Negatron-master Negatron && pip install tensorflow pydantic && rm -rf ./Negatron/models/mutcompute1 && \
    unzip /dependencies/ApBioInformatics-master.zip && rm /dependencies/ApBioInformatics-master.zip && mv ./ApBioInformatics-master ApBioInformatics && pip install ./ApBioInformatics

RUN pip install boto3

WORKDIR /predictor

ENV PYTHONPATH=/usr/local/lib:/apchem/Negatron

COPY predictor .