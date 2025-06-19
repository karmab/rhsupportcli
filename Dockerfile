FROM alpine:3.17

MAINTAINER Karim Boumedhel <karimboumedhel@gmail.com>

LABEL name="karmab/rhsupportcli" \
      maintainer="karimboumedhel@gmail.com" \
      vendor="Karmalabs" \
      version="latest" \
      release="0" \
      summary="RH Support cli" \
      description="RH Support cli"

RUN apk add --update --no-cache python3-dev openssl py3-pip

RUN mkdir /root/rhsupportcli
ADD README.md /root/rhsupportcli
ADD src /root/rhsupportcli/src
COPY pyproject.toml /root/rhsupportcli
RUN pip3 install -U pip setuptools wheel build && pip3 install -e /root/rhsupportcli
RUN touch /i_am_a_container

ENTRYPOINT ["/usr/bin/rhsupportcli"]
CMD ["-h"]
