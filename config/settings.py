from environs import Env
from dataclasses import dataclass

@dataclass
class Db:
    db_user: str
    db_password: str
    db_database: str
    db_host: str
    db_port: int
    table_tasks:str
    table_datas:str

@dataclass
class Logs:
    level: str
    dir: str
    format: str
    separate_log_without_rollover: bool

@dataclass
class Driver:
    chrome_version: int
    debug: bool

@dataclass
class Settings:
    db: Db
    logs: Logs
    driver: Driver

def get_settings(path: str):
    env = Env()
    env.read_env(path, override=True)

    return Settings(
        db=Db(
            db_user=env.str('DB_USER'),
            db_password=env.str('DB_PASSWORD'),
            db_database=env.str('DB_DATABASE'),
            db_host=env.str('DB_HOST'),
            db_port=env.int('DB_PORT'),
            table_tasks='navigates_gates_task',
            table_datas='navigates_gates_data',
        ),
        logs=Logs(
            level=env.str('LOGS_LEVEL'),
            dir=env.str('LOGS_DIR'),
            format=env.str('LOGS_FORMAT'),
            separate_log_without_rollover=env.str('LOGS_ROLLOVER')
        ),
        driver=Driver(
            chrome_version=env.int('DRIVER_VERSION'),
            debug=env.bool('DEBUG')
        )
    )

settings = get_settings('.env')
