ARG PG_MAJOR=17
ARG DEBIAN_CODENAME=bookworm
ARG PGVECTOR_VERSION=v0.8.2

FROM postgres:${PG_MAJOR}-${DEBIAN_CODENAME} AS builder
ARG PG_MAJOR
ARG PGVECTOR_VERSION

ADD https://github.com/pgvector/pgvector.git#${PGVECTOR_VERSION} /tmp/pgvector

RUN apt-get update && \
    apt-mark hold locales && \
    apt-get install -y --no-install-recommends build-essential postgresql-server-dev-${PG_MAJOR} && \
    cd /tmp/pgvector && \
    make clean && \
    make OPTFLAGS="" && \
    make install DESTDIR=/tmp/pgvector-install && \
    mkdir -p /tmp/pgvector-install/usr/share/doc/pgvector && \
    cp LICENSE README.md /tmp/pgvector-install/usr/share/doc/pgvector && \
    rm -r /tmp/pgvector && \
    apt-get remove -y build-essential postgresql-server-dev-${PG_MAJOR} && \
    apt-get autoremove -y && \
    apt-mark unhold locales && \
    rm -rf /var/lib/apt/lists/*

FROM postgres:${PG_MAJOR}-${DEBIAN_CODENAME}
ARG PG_MAJOR

COPY --from=builder /tmp/pgvector-install/usr/lib/postgresql/${PG_MAJOR}/lib/vector.so /usr/lib/postgresql/${PG_MAJOR}/lib/
COPY --from=builder /tmp/pgvector-install/usr/share/postgresql/${PG_MAJOR}/extension/vector.control /usr/share/postgresql/${PG_MAJOR}/extension/
COPY --from=builder /tmp/pgvector-install/usr/share/postgresql/${PG_MAJOR}/extension/vector--*.sql /usr/share/postgresql/${PG_MAJOR}/extension/
COPY --from=builder /tmp/pgvector-install/usr/share/doc/pgvector /usr/share/doc/pgvector