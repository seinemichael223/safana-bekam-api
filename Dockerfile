FROM python:3

WORKDIR /reknown-material

COPY requirements.txt requirements.txt 
RUN pip3 install -r requirements.txt


COPY . .

CMD ["python3", "run.py"]
