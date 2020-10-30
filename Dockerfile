FROM python:3.8.6

MAINTAINER StephenEvenson stephen.zrt@qq.com

COPY ./* /code/
WORKDIR /code
RUN pip3 install -r requirement.txt
EXPOSE 8080

CMD ["python3","/code/app.py"]
