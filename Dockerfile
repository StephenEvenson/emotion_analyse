FROM python:3.8.6

MAINTAINER StephenEvenson stephen.zrt@qq.com

COPY ./* /code/
WORKDIR /code
RUN pip333 install -r requirements.txt
EXPOSE 8080

CMD ["python3","/code/app.py"]
