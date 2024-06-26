FROM postgis/postgis:16-3.4

RUN apt-get update -y
RUN apt-get install git make build-essential postgresql-server-dev-16 -y
RUN apt-get clean
RUN rm -rf /var/cache/apt/lists

RUN git clone https://github.com/pgpartman/pg_partman && cd pg_partman && make install