FROM python:3.8-slim-buster

WORKDIR /app

ENV MONGO_URI=mongodb://mongodb:27017
ENV NEO4J_URI=bolt://neo4j:7687
ENV NEO4J_USERNAME=neo4j
ENV NEO4J_PASSWORD=supersecret

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY app.py app.py
COPY datasets datasets
COPY scripts scripts
COPY src src

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
