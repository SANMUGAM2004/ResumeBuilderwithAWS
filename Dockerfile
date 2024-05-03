FROM python:3.10.12

WORKDIR /ResumeBuilderwithAWS

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "resumebuilder.py"]
