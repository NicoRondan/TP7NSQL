FROM python:latest
WORKDIR /src
COPY . /src
RUN pip3 install flask pymongo requests
EXPOSE 5000