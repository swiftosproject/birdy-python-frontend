import requests
import json
import argparse
from getpass import getpass

parser = argparse.ArgumentParser()
parser.add_argument("--fetch", nargs=2, help="Fetch a package")
parser.add_argument("--publish", nargs=4, help="Publish a package")
parser.add_argument("--register", action="store_const", const=True, help="Register a new user")
parser.add_argument("--dependencies", nargs=2, help="Get package dependencies")

args = parser.parse_args()
auth_token = None

def register(username, password):
    response = requests.post(
        'http://localhost:5000/register', 
        json={'username': username, 'password': password}
    )
    print(response.text)

def login(username, password):
    global auth_token
    response = requests.post(
        'http://localhost:5000/login', 
        json={'username': username, 'password': password}
    )
    if response.status_code == 200:
        auth_token = response.cookies.get('session')
        print('Login successful')
    else:
        print('\033[31mLogin failed\033[0m')

def publish():
    username = input("Username: ")
    password = getpass("Password: ")

    login(username, password)

    filename = args.publish[0]
    name = args.publish[1]
    version = args.publish[2]
    description = args.publish[3]

    package_data = {
        'name': name,
        'author': username,
        'version': version,
        'description': description
    }

    data = {
        'json': json.dumps(package_data),
    }

    try:
        with open(filename, 'rb') as package:
            files = {'file': (filename, package)}
            response = requests.post(
                'http://localhost:5000/publish', 
                files=files, 
                data=data,
                cookies={'session': auth_token}
            )
            print(response.text)
    except FileNotFoundError:
        print(f"\033[31mFile {filename} not found!\033[0m")

def download_file(url, destination):
    response = requests.get(url)
    if response.status_code == 200:
        with open(destination, 'wb') as f:
            f.write(response.content)
        print(f"File downloaded successfully to {destination}")
    else:
        print(f"\033[31mFailed to download file from {url}\033[0m")

def fetch_latest_version(name):
    try:
        response = requests.get(f"http://localhost:5000/packages/{name}.json")
        response.raise_for_status()
        return response.json()['version']
    except requests.RequestException as e:
        print(f"\033[31mError fetching latest version for {name}: {e}\033[0m")
    return None

def get_dependencies(name, version):
    try:
        response = requests.get(f"http://localhost:5000/packages/{name}-{version}/dependencies")
        response.raise_for_status()
        dependencies = response.json()
        if dependencies:
            print(f"Dependencies for {name} version {version}:")
            for dependency in dependencies:
                print(f"  - {dependency}")
        else:
            print(f"No dependencies for {name} version {version}.")
    except requests.RequestException as e:
        print(f"\033[31mError fetching dependencies for {name} version {version}: {e}\033[0m")

if args.publish:
    publish()

if args.register:
    username = input("Username: ")
    password = getpass("Password: ")
    register(username, password)

if args.fetch:
    name = args.fetch[0]
    output = args.fetch[1]
    if "-" not in name:
        version = fetch_latest_version(name)
    else:
        name, version = name.split('-')
    download_file(f"http://localhost:5000/packages/{name}-{version}.tar.xz", output)

if args.dependencies:
    name = args.dependencies[0]
    version = args.dependencies[1]
    get_dependencies(name, version)
