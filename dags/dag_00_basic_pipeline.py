from __future__ import annotations

import os
import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.models.xcom_arg import XComArg

# CustomOperator
from plugins.operators.word_count_operator import WordCountOperator

TZ = "America/Bogota"
local_tz = pendulum.timezone(TZ)

default_args = {
    "owner": "brian",
    "retries": 0,
}

with DAG(
    dag_id="basic_pipeline",
    description="Pipeline básico con Bash/Python, XComs, CustomOperator y trigger_rules",
    default_args=default_args,
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz=local_tz),
    catchup=False,
    tags=["demo", "basics", "xcom", "custom"],
) as dag:

    hello_bash = BashOperator(
        task_id="hello_bash",
        bash_command='echo "Hola desde BashOperator 👋"',
    )

    def extract_data(**context):
        payload = {
            "records": 100,
            "path": "/opt/airflow/data/tmp/data.csv",
        }
        return payload

    extract = PythonOperator(
        task_id="extract",
        python_callable=extract_data,
    )

    push_from_bash = BashOperator(
        task_id="push_from_bash",
        bash_command='echo "42"',
        do_xcom_push=True,
    )

    def write_sample_text(**_):
        path = "/opt/airflow/data/tmp/sample.txt"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("Airflow nos permite orquestar pipelines de datos de forma reproducible y confiable.")
        return path

    write_text = PythonOperator(
        task_id="write_sample_text",
        python_callable=write_sample_text,
    )

    word_count = WordCountOperator(
        task_id="count_words",
        filepath="/opt/airflow/data/tmp/sample.txt",
    )

    def transform_data(**context):
        ti = context["ti"]
        extracted = ti.xcom_pull(task_ids="extract")
        records = int(extracted["records"])
        bash_value = int(ti.xcom_pull(task_ids="push_from_bash"))
        total = records + bash_value  # 100 + 42 = 142
        return {"total": total}

    transform = PythonOperator(
        task_id="transform",
        python_callable=transform_data,
    )

    def report_total(total_dict: dict, word_count_value: int, **_):
        print(f"[Reporte] Total calculado = {total_dict['total']}, palabras en archivo = {word_count_value}")

    report = PythonOperator(
        task_id="report",
        python_callable=report_total,
        op_args=[XComArg(transform), XComArg(word_count)],
    )

    join_ok = EmptyOperator(
        task_id="join_ok",
        trigger_rule="none_failed_min_one_success",
    )

    cleanup_on_failure = BashOperator(
        task_id="cleanup_on_failure",
        bash_command='echo "Limpiando recursos tras un fallo..."',
        trigger_rule="one_failed",
    )

    always_finalize = BashOperator(
        task_id="always_finalize",
        bash_command='echo "Fin del pipeline (all_done)"',
        trigger_rule="all_done",
    )

    hello_bash >> extract
    extract >> [push_from_bash, write_text]
    write_text >> word_count
    [push_from_bash, word_count] >> transform >> report
    [report, word_count, transform] >> join_ok
    [report, word_count, transform] >> cleanup_on_failure
    [join_ok, cleanup_on_failure] >> always_finalize
