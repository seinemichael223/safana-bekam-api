FROM python:3.12

WORKDIR /safana-bekam-api

COPY requirements.txt requirements.txt 
RUN pip3 install -r requirements.txt


COPY . .

CMD ["python3", "run.py"]
