FROM python:3.9

ENV PORT=8080

RUN mkdir /app
RUN chown -R nobody /app
COPY . /app
VOLUME /app
WORKDIR /app

RUN pip install .

USER nobody
CMD exec gunicorn -w 1 -b 0.0.0.0:$PORT template_python.main:app

EXPOSE $PORT
