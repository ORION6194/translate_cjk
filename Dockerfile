FROM python:3.7.4-alpine3.10

ADD ./translation ./translation/

RUN apk upgrade
RUN apk update
RUN apk add --no-cache gcc musl-dev bind-tools libxml2 libxml2-dev libxslt-dev
RUN pip install cython
RUN apk update
RUN pip install -r requirements.txt

CMD ["python3", "-u", "translation/main.py"]
