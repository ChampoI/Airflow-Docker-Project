from __future__ import annotations

import random
import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.branch import BranchPythonOperator
from airflow.operators.empty import EmptyOperator

TZ = "America/Bogota"
local_tz = pendulum.timezone(TZ)

default_args = {"owner": "brian"}

with DAG(
    dag_id="branching_example",
    description="Ejemplo de BranchPythonOperator con merge posterior",
    default_args=default_args,
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz=local_tz),
    catchup=False,
    tags=["branching"],
) as dag:

    def generate_metric(**_):
        value = random.randint(0, 100)
        return value

    gen = PythonOperator(
        task_id="generate_metric",
        python_callable=generate_metric,
    )

    def decide_branch(**context):
        ti = context["ti"]
        value = int(ti.xcom_pull(task_ids="generate_metric"))
        if value < 50:
            return "process_small"
        return "process_large"

    branch = BranchPythonOperator(
        task_id="branch_logic",
        python_callable=decide_branch,
    )

    process_small = PythonOperator(
        task_id="process_small",
        python_callable=lambda **_: print("Procesando rama SMALL (<50)"),
    )

    process_large = PythonOperator(
        task_id="process_large",
        python_callable=lambda **_: print("Procesando rama LARGE (>=50)"),
    )

    merge = EmptyOperator(
        task_id="merge_branches",
        trigger_rule="none_failed_min_one_success",
    )

    gen >> branch
    branch >> [process_small, process_large] >> merge
