FROM apache/airflow:2.10.1
USER root
RUN pip install --no-cache-dir pendulum==3.0.0
USER airflow
