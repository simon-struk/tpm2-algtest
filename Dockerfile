FROM fedora:29
RUN dnf install --assumeyes \
        clang cmake make tpm2-tss-devel tpm2-tools openssl-devel
COPY . /tpm2-algtest
WORKDIR /tpm2-algtest/build
RUN cmake .. && make
ENTRYPOINT ["./tpm2_algtest"]
