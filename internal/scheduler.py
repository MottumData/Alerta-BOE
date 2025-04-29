import datetime
import win32com.client

def register_daily_task(exe_path: str, task_name: str = "EnviarNewsletter") -> None:

    """
    Registra o actualiza una tarea diaria en el Programador de Tareas de Windows
    para ejecutar un archivo .exe a diario.

    Args:
        exe_path (str): Ruta absoluta al ejecutable que se desea programar.
        task_name (str, optional): Nombre que recibirá la tarea en el Programador.
                                   Por defecto es "EnviarNewsletter".

    Returns:
        None

    Instructions:
        - Añadir un módulo scheduler.py a tu repo que, al ejecutarse, se conecta al Task Scheduler, crea o actualiza el trigger diario y registra la acción de llamar a tu exe 

        - Empaquetar todo en un .exe con PyInstaller usando --onefile y --uac-admin para que solicite elevación sin que el usuario toque nada pyinstaller.org

        - Probar localmente, subir dist/tu_app.exe al repositorio (o un release) y enviar por email ese único archivo. El destinatario hace doble clic, acepta la elevación y ya queda registrada la tarea diaria.
        
        - Para crear el ejecutable -> pyinstaller --onefile --windowed --uac-admin --name NewsletterApp scheduler.py

    """
    # 1. Conectar al servicio
    scheduler = win32com.client.Dispatch("Schedule.Service")
    scheduler.Connect()  # :contentReference[oaicite:4]{index=4}

    # 2. Carpeta raíz
    root = scheduler.GetFolder("\\")  # :contentReference[oaicite:5]{index=5}

    # 3. Nueva definición
    task_def = scheduler.NewTask(0)    # :contentReference[oaicite:6]{index=6}
    task_def.RegistrationInfo.Description = "Envío diario de newsletter"

    # 4. Trigger diario
    trigger = task_def.Triggers.Create(2)  # 2 = TASK_TRIGGER_DAILY :contentReference[oaicite:7]{index=7}
    # Empieza dentro de 1 minuto
    start = (datetime.datetime.now() + datetime.timedelta(minutes=1)) \
            .strftime("%Y-%m-%dT%H:%M:%S")
    trigger.StartBoundary = start
    trigger.DaysInterval = 1

    # 5. Acción: ejecutar el propio exe
    action = task_def.Actions.Create(0)  # 0 = TASK_ACTION_EXEC :contentReference[oaicite:8]{index=8}
    action.Path = exe_path
    action.WorkingDirectory = exe_path.rsplit("\\", 1)[0]

    # 6. Registrar o actualizar
    # 6 = TASK_CREATE_OR_UPDATE, 3 = TASK_LOGON_NONE
    root.RegisterTaskDefinition(task_name, task_def, 6, None, None, 3)
    print(f"Tarea '{task_name}' programada con éxito.")

if __name__ == "__main__":
    import sys
    # Recepción de la ruta al exe desde sys.argv[1]
    exe = sys.argv[1] if len(sys.argv) > 1 else sys.executable
    register_daily_task(exe)
