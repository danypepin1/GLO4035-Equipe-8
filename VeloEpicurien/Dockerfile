FROM python:3.8-slim-buster

WORKDIR /app
ENV MONGO_URI=mongodb://mongodb:27017

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY app.py app.py
COPY datasets datasets
COPY scripts scripts
COPY src src

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
