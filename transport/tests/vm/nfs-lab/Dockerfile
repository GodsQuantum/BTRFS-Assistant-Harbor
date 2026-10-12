FROM ubuntu:26.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends nfs-ganesha nfs-ganesha-mem rpcbind && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /run/ganesha
COPY ganesha.conf /etc/ganesha/ganesha.conf
EXPOSE 2049
CMD ["/bin/sh","-c","/sbin/rpcbind -w && exec /usr/bin/ganesha.nfsd -F -L STDERR -f /etc/ganesha/ganesha.conf"]
