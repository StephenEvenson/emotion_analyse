FROM python:3.8.6

MAINTAINER StephenEvenson stephen.zrt@qq.com

ADD https://github.com/StephenEvenson/emotion_analyse/archive/v1.tar.gz /code/
WORKDIR /code/emotion_analyse-1
RUN pip3 install -r requirement.txt
EXPOSE 8080

CMD ["python3","/code/app.py"]
