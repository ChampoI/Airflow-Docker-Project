from __future__ import annotations

import os
import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

TZ = "America/Bogota"
local_tz = pendulum.timezone(TZ)

default_args = {"owner": "brian"}

with DAG(
    dag_id="producer_dag",
    description="DAG productor: crea artefactos y termina en task 'producer_complete'",
    default_args=default_args,
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz=local_tz),
    catchup=False,
    tags=["external", "producer"],
) as dag:

    def produce_dataset(**_):
        path = "/opt/airflow/data/tmp/producer.done"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("done")
        return path

    produce = PythonOperator(
        task_id="produce_dataset",
        python_callable=produce_dataset,
    )

    producer_complete = EmptyOperator(task_id="producer_complete")

    produce >> producer_complete
