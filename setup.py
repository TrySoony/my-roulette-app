import os
import shutil

def setup_project():
    # Создание директорий
    directories = ['static', 'assets']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

    # Перемещение изображений
    if os.path.exists('images'):
        for file in os.listdir('images'):
            src = os.path.join('images', file)
            dst = os.path.join('assets', file)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                print(f"Copied {file} to assets/")

if __name__ == "__main__":
    setup_project() 