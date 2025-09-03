# 🚀 Airflow + Docker Demo Project

Este proyecto demuestra cómo orquestar flujos de trabajo en **Apache Airflow** usando **Docker** y **Visual Studio Code**.  
Incluye ejemplos prácticos de distintos tipos de operadores, sensores, reglas de ejecución, paso de datos entre tareas y branching, todo con código limpio, comentado y fácilmente replicable.

---

## 📂 Estructura del proyecto

```
airflow-docker-vscode/
├─ .env                   # Variables de entorno (UID/GID)
├─ docker-compose.yml     # Orquestación de servicios (Airflow, Postgres)
├─ Dockerfile             # Imagen personalizada con dependencias extra
├─ requirements.txt       # Dependencias Python adicionales
├─ logs/                  # Logs de Airflow
├─ data/
│  ├─ incoming/           # Archivos externos (para FileSensor)
│  └─ tmp/                # Archivos temporales generados en DAGs
├─ dags/
│  ├─ dag_00_basic_pipeline.py
│  ├─ dag_01_file_sensors.py
│  ├─ dag_02_producer.py
│  ├─ dag_03_consumer_external_sensor.py
│  └─ dag_04_branching.py
└─ plugins/
   └─ operators/
      └─ word_count_operator.py
```

---

## ⚙️ Requisitos previos

- **Docker** y **Docker Compose**
- **Visual Studio Code** con extensiones recomendadas:
  - Docker
  - Python
  - Dev Containers (opcional)

---

## ▶️ Ejecución desde VS Code

1. **Abrir proyecto en VS Code**  
   `File > Open Folder...` → seleccionar `airflow-docker-vscode`.

2. **Configurar archivo `.env`**  
   - Linux/Mac:  
     ```bash
     echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" > .env
     ```  
   - Windows (manual):  
     ```
     AIRFLOW_UID=50000
     AIRFLOW_GID=0
     ```

3. **Inicializar base de datos y crear usuario admin**  
   ```bash
   docker compose up airflow-init
   ```

4. **Levantar servicios principales (scheduler, webserver, triggerer, postgres)**  
   ```bash
   docker compose up -d
   ```

5. **Acceder a la interfaz de Airflow**  
   - URL: [http://localhost:8080](http://localhost:8080)  
   - Usuario: `admin`  
   - Contraseña: `admin`

6. **Ejecutar DAGs desde la UI**  
   Activa y corre los DAGs de ejemplo (`basic_pipeline`, `file_sensors`, etc.) para observar el comportamiento.

7. **Detener servicios cuando termines**  
   ```bash
   docker compose down
   ```

---

## 🛠️ ¿Qué se implementó?

El proyecto incluye varios casos prácticos, cada uno ilustrando un concepto clave de Airflow.

### 1️⃣ BashOperator y PythonOperator

Archivo: `dags/dag_00_basic_pipeline.py`

```python
hello_bash = BashOperator(
    task_id="hello_bash",
    bash_command='echo "Hola desde BashOperator 👋"',
)

def extract_data(**context):
    return {"records": 100, "path": "/opt/airflow/data/tmp/data.csv"}

extract = PythonOperator(
    task_id="extract",
    python_callable=extract_data,
)
```

📌 **Sugerencia de ejecución:**  
Corre el DAG `basic_pipeline` y observa cómo `extract` devuelve un diccionario que luego se usa en transformaciones.

---

### 2️⃣ XComs (Cross-Communications)

En el mismo DAG:

```python
push_from_bash = BashOperator(
    task_id="push_from_bash",
    bash_command='echo "42"',
    do_xcom_push=True,  # Envía el valor a XCom
)

def transform_data(**context):
    ti = context["ti"]
    extracted = ti.xcom_pull(task_ids="extract")
    bash_value = int(ti.xcom_pull(task_ids="push_from_bash"))
    return {"total": extracted["records"] + bash_value}
```

📌 **Sugerencia de ejecución:**  
Desde la UI de Airflow, abre la vista de XComs y revisa cómo se pasan datos entre tareas.

---

### 3️⃣ Custom Operator

Archivo: `plugins/operators/word_count_operator.py`

```python
class WordCountOperator(BaseOperator):
    template_fields = ("filepath",)

    def execute(self, context):
        with open(self.filepath, "r", encoding="utf-8") as f:
            text = f.read()
        return len(text.split())
```

📌 **Sugerencia de ejecución:**  
Ejecuta la tarea `count_words` en el DAG `basic_pipeline` y observa cómo retorna el conteo de palabras de un archivo generado previamente.

---

### 4️⃣ Trigger Rules

En `basic_pipeline` se configuran distintos escenarios:

```python
join_ok = EmptyOperator(
    task_id="join_ok",
    trigger_rule="none_failed_min_one_success",
)

cleanup_on_failure = BashOperator(
    task_id="cleanup_on_failure",
    bash_command='echo "Limpiando tras fallo"',
    trigger_rule="one_failed",
)

always_finalize = BashOperator(
    task_id="always_finalize",
    bash_command='echo "Pipeline finalizado"',
    trigger_rule="all_done",
)
```

📌 **Sugerencia de ejecución:**  
Forza fallos en algunas tareas y revisa qué rutas se ejecutan según la regla de disparo.

---

### 5️⃣ FileSensor

Archivo: `dags/dag_01_file_sensors.py`

```python
wait_external_flag = FileSensor(
    task_id="wait_external_flag",
    fs_conn_id="fs_default",
    filepath="incoming/external_ready.flag",
    poke_interval=10,
    timeout=600,
    mode="reschedule",
)
```

📌 **Sugerencia de ejecución:**  
Crea un archivo desde tu host:  
```bash
echo listo > data/incoming/external_ready.flag
```

El DAG continuará al detectarlo.

---

### 6️⃣ ExternalTaskSensor

`consumer_dag` espera a `producer_dag`:

```python
wait_for_producer = ExternalTaskSensor(
    task_id="wait_for_producer",
    external_dag_id="producer_dag",
    external_task_id="producer_complete",
    allowed_states=["success"],
)
```

📌 **Sugerencia de ejecución:**  
Ejecuta primero `producer_dag` y luego activa `consumer_dag`. Verás cómo espera la finalización antes de continuar.

---

### 7️⃣ BranchPythonOperator

Archivo: `dags/dag_04_branching.py`

```python
def decide_branch(**context):
    value = context["ti"].xcom_pull(task_ids="generate_metric")
    return "process_small" if value < 50 else "process_large"

branch = BranchPythonOperator(
    task_id="branch_logic",
    python_callable=decide_branch,
)
```

📌 **Sugerencia de ejecución:**  
Cada ejecución elegirá una rama diferente (según un valor aleatorio). El flujo se unifica con un `merge` que usa `trigger_rule`.

---

## ✅ Conclusión

Este proyecto te guía en la práctica de conceptos clave de Airflow:

- Operadores básicos y personalizados
- Comunicación entre tareas (XComs)
- Reglas de disparo (trigger rules)
- Sensores para archivos y dependencias externas
- Ramas condicionales en DAGs

Es un punto de partida sólido para proyectos reales de orquestación de datos.
