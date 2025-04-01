FROM python:3.12-slim 
RUN pip install --upgrade pip 
COPY r.txt . 
RUN pip install --no-cache-dir -r r.txt 
WORKDIR /app 
COPY . . 
ENTRYPOINT [ "python","init.py" ]
CMD ["python","main.py"]