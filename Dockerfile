FROM python:3.7.2-stretch

RUN mkdir /webapp
ADD entrypoint.sh /webapp
ADD ./src /webapp

WORKDIR /webapp

RUN pip install --upgrade --no-cache-dir pip && pip install --no-cache-dir -r requirements.txt

#EXPOSE 5000
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
