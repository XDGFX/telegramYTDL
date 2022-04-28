FROM python:3.8

RUN apt update && apt install -y ffmpeg

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "." ]