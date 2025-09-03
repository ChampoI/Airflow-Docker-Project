from __future__ import annotations

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.sensors.external_task import ExternalTaskSensor

TZ = "America/Bogota"
local_tz = pendulum.timezone(TZ)

default_args = {"owner": "brian"}

with DAG(
    dag_id="consumer_dag",
    description="DAG consumidor que espera a producer_dag via ExternalTaskSensor",
    default_args=default_args,
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz=local_tz),
    catchup=False,
    tags=["external", "consumer"],
) as dag:

    wait_for_producer = ExternalTaskSensor(
        task_id="wait_for_producer",
        external_dag_id="producer_dag",
        external_task_id="producer_complete",
        allowed_states=["success"],
        failed_states=["failed", "skipped"],
        poke_interval=15,
        timeout=60 * 10,
        mode="reschedule",
    )

    consume = BashOperator(
        task_id="consume_artifact",
        bash_command='echo "Consumidor: el productor terminó. Continuamos con el proceso..."',
    )

    wait_for_producer >> consume
