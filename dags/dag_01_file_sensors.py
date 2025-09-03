from __future__ import annotations

import os
import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor

TZ = "America/Bogota"
local_tz = pendulum.timezone(TZ)

default_args = {"owner": "brian"}

with DAG(
    dag_id="file_sensors",
    description="Ejemplos de FileSensor (local y externo)",
    default_args=default_args,
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz=local_tz),
    catchup=False,
    tags=["sensors", "files"],
) as dag:

    def create_local_flag(**_):
        path = "/opt/airflow/data/tmp/ready.flag"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("ok")
        return path

    create_flag = PythonOperator(
        task_id="create_local_flag",
        python_callable=create_local_flag,
    )

    wait_local_flag = FileSensor(
        task_id="wait_local_flag",
        fs_conn_id="fs_default",
        filepath="tmp/ready.flag",
        poke_interval=10,
        timeout=60 * 5,
        mode="reschedule",
    )

    process_local = BashOperator(
        task_id="process_local",
        bash_command='echo "Procesando archivo local detectado por FileSensor..."',
    )

    wait_external_flag = FileSensor(
        task_id="wait_external_flag",
        fs_conn_id="fs_default",
        filepath="incoming/external_ready.flag",
        poke_interval=10,
        timeout=60 * 10,
        mode="reschedule",
    )

    process_external = BashOperator(
        task_id="process_external",
        bash_command='echo "Procesando archivo externo (host) detectado por FileSensor..."',
    )

    create_flag >> wait_local_flag >> process_local
    wait_external_flag >> process_external
