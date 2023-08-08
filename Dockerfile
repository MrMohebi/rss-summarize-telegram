FROM python
COPY requirements.txt requirements.txt

RUN pip install --upgrade pip --index-url http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
RUN pip config set global.index-url http://mirrors.aliyun.com/pypi/simple/

RUN pip install -r requirements.txt --trusted-host mirrors.aliyun.com
COPY . .
CMD ["python", "-u", "main.py"]
