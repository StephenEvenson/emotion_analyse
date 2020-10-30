FROM python:3.8.6

MAINTAINER StephenEvenson stephen.zrt@qq.com

ADD https://github.com/StephenEvenson/emotion_analyse/archive/master.zip /code/
WORKDIR /code/emotion_analyse-master
RUN unzip /code/master.zip -d /code/ && pip3 install -r requirement.txt
EXPOSE 8080

CMD ["python3","/code/emotion_analyse-master/app.py"]
