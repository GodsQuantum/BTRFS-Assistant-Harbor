FROM ubuntu:26.04 AS build
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y --no-install-recommends build-essential autoconf automake libtool flex bison libtirpc-dev pkg-config git > /tmp/deps 2>&1
COPY unfs3 /src
WORKDIR /src
RUN ./bootstrap && ./configure --prefix=/usr && make -j4
FROM ubuntu:26.04
RUN apt-get update -qq && apt-get install -y --no-install-recommends libtirpc3t64 rpcbind && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/unfsd /usr/local/sbin/unfsd
EXPOSE 2049 20048 111
CMD ["sh","-c","rpcbind -w && exec /usr/local/sbin/unfsd -d -e /tmp/exports"]
