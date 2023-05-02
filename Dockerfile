FROM ubuntu:latest
COPY . .

RUN pip install -r requirements.txt
CMD ./docker_entrypoint.sh