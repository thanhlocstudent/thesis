FROM tiangolo/uwsgi-nginx-flask:python3.6

COPY ./InformationGathering /app
RUN pip3 install requests
RUN pip3 install dnsdumpster
ENTRYPOINT ["/bin/bash", "-c", "python3 __init__.py"]

