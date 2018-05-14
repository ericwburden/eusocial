import docker
import bcrypt
from time import sleep
from datetime import datetime
from cryptography.fernet import Fernet


def get_admin_pwd_hash(pwd):
    salt = bcrypt.gensalt(14, prefix=b'2a')
    pwd_bytes = pwd.encode('utf-8')
    pwd_hashed = bcrypt.hashpw(
        pwd_bytes,
        salt
    )
    return(pwd_hashed, salt)


def clear_db_container(client):
    try:
        container = client.containers.get('eusocial-testdb')
        container.stop()
    except docker.errors.NotFound:
        print('No container found.')
    finally:
        client.containers.prune()


def new_db_container(client):
    container = client.containers.run(
        'mongo',
        name='eusocial-testdb',
        detach=True,
        ports={'27017': 27017}
    )
    sleep(5)
    x = container.exec_run(
        (
            'mongo test --eval "db.createUser({'
            "user: 'testuser', "
            "pwd: 'testpwd', "
            "roles: [{role: 'readWrite', db: 'test'}]"
            '});"'
        )
    )
    print(x[1].decode("utf-8"))
    pwd = get_admin_pwd_hash('boogers')
    y = container.exec_run(
        (
            'mongo test --eval "db.api_users.insert({'
            "email: 'admin@eusoci.al', "
            "password: '" + pwd[0].decode('utf-8') + "',"
            "role: 'owner',"
            "organization: 'eusocial',"
            "program: 'eusocial',"
            "created: '" + str(datetime.utcnow()) + "',"
            "services: []"
            '});"'
        )
    )
    print(y[1].decode("utf-8"))
    client.close()


def gen_fernet_key():
    key = Fernet.generate_key()
    with open('../keys/fernet.key', 'w') as key_file:
        key_file.write(key.decode('utf-8'))


def reload_db():
    gen_fernet_key()
    client = docker.from_env()
    clear_db_container(client)
    new_db_container(client)


if __name__ == '__main__':
    client = docker.from_env()
    clear_db_container(client)
    new_db_container(client)
