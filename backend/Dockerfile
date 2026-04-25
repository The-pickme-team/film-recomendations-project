FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY ./requirements.txt ./
RUN pip install -r requirements.txt

COPY ./src ./src
COPY ./run.sh ./

RUN chmod +x ./run.sh
ENTRYPOINT ["./run.sh"]