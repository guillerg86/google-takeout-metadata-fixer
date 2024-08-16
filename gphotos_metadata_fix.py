from datetime import datetime
from win32_setctime import setctime
import argparse
import os
import re
from pyexiv2 import Image as ImgMeta
import json

MONTHS = 2
DIFF_BETWEEN_CREATEDTIME_PHOTOTAKENTIME_SECONDS = MONTHS * 30 * 86400

## FUNCIONES MODIFICAR METADATOS
def set_metadata_date_to_image_file(image,date):
    date_string = date.strftime("%Y:%m:%d %H:%M:%S")
    with ImgMeta(image) as img_meta:
        exif = img_meta.read_exif()
        img_meta.modify_exif({'Exif.Image.DateTime': date_string})
        img_meta.modify_exif({'Exif.Image.DateTimeOriginal': date_string})
        img_meta.modify_exif({'Exif.Photo.DateTimeDigitized': date_string})
        img_meta.modify_exif({'Exif.Photo.DateTimeOriginal': date_string})
        img_meta.modify_exif({'Exif.Thumbnail.DateTime': date_string})
        if exif.get('Exif.SonySInfo1.SonyDateTime',None):
            img_meta.modify_exif({'Exif.SonySInfo1.SonyDateTime': date_string})

def set_created_time(image,timestamp):
    setctime(image, timestamp)
    os.utime(image, (timestamp, timestamp))

def fix_image_name_format_1(image_path,image_name):
    # IMAGE FORMAT EXAMPLE - IMG_20230728_223352*****
    splitted_image_name = image_name.split('_')
    date = splitted_image_name[1]
    time = splitted_image_name[2]
    image_dt = datetime(
        int(date[0:4]), 
        int(date[4:6]), 
        int(date[6:8]), 
        int(time[0:2]),
        int(time[2:4]), 
        int(time[4:6])
    )
    timestamp = datetime.timestamp(image_dt)
    set_created_time(image_path,timestamp)
    set_metadata_date_to_image_file(image_path,image_dt)
    
def fix_image_name_format_2(image_path,image_name):
    # IMAGE FORMAT EXAMPLE - 20230728_223352*****
    splitted_image_name = image_name.split('_')
    date = splitted_image_name[0]
    time = splitted_image_name[1]
    image_dt = datetime(
        int(date[0:4]), 
        int(date[4:6]), 
        int(date[6:8]), 
        int(time[0:2]),
        int(time[2:4]), 
        int(time[4:6])
    )
    timestamp = datetime.timestamp(image_dt)
    set_created_time(image_path,timestamp)
    set_metadata_date_to_image_file(image_path,image_dt)

def fix_image_name_format_3(image_path,image_name):
    # IMAGE FORMAT EXAMPLE - Screenshot_2019-04-09-09-30-17*****
    splitted_image_name = image_name.split('-')
    year = (splitted_image_name[0].split('_'))[1]
    month = splitted_image_name[1]
    day = splitted_image_name[2]
    hour = splitted_image_name[3]
    minute = splitted_image_name[4]
    seconds = splitted_image_name[5]
    image_dt = datetime(
        int(year), 
        int(month), 
        int(day), 
        int(hour),
        int(minute), 
        int(seconds)
    )
    timestamp = datetime.timestamp(image_dt)
    set_created_time(image_path,timestamp)
    set_metadata_date_to_image_file(image_path,image_dt)

def fix_image_name_format_4(image_path,image_name):
    # IMAGE FORMAT EXAMPLE - IMG-20181205-WA0002*****
    splitted_image_name = image_name.split('-')
    date = splitted_image_name[1]
    image_dt = datetime(
        int(date[0:4]), 
        int(date[4:6]), 
        int(date[6:8]), 
        0,0,0
    )
    timestamp = datetime.timestamp(image_dt)
    set_created_time(image_path,timestamp)
    set_metadata_date_to_image_file(image_path,image_dt)    


def fix_image(image,level=0):
    image_name = (image.split('\\'))[-1]
    #print(f"{'\t'*level}Procesando imagen {image_name} ")

    if re.search(r"^IMG_\d{8}_\d{6}",image_name):
        print(f"{'\t'*level}Procesando imagen {image_name} ")
        fix_image_name_format_1(image,image_name)
        return
    
    if re.search(r"^\d{8}_\d{6}",image_name):
        print(f"{'\t'*level}Procesando imagen {image_name} ")
        fix_image_name_format_2(image,image_name)
        return

    if re.search(r"Screenshot_\d{4}(\-\d{2}){5,}",image_name):
        print(f"{'\t'*level}Procesando imagen {image_name} ")
        fix_image_name_format_3(image,image_name)
        return

    if re.search(r"IMG\-\d{8}\-WA\d+",image_name):
        print(f"{'\t'*level}Procesando imagen {image_name} ")
        fix_image_name_format_4(image,image_name)
        return

    if not os.path.exists(f"{image}.json"):
        # No existe JSON y por lo tanto no tenemos metadatos a cargar... no tocamos la foto
        print(f"{'\t'*level}Descartando imagen {image} -> No se encuentra json")
        return
    
    print(f"{'\t'*level}Procesando imagen {image_name} ")
    metadata = json.load(open(f"{image}.json"))
    created_timestamp = float(metadata.get('creationTime').get('timestamp'))
    phototaken_time = float(metadata.get('photoTakenTime').get('timestamp'))
    if phototaken_time < created_timestamp and (created_timestamp-phototaken_time) < DIFF_BETWEEN_CREATEDTIME_PHOTOTAKENTIME_SECONDS:
        timestamp = phototaken_time
    else:
        timestamp = created_timestamp 
    date = datetime.fromtimestamp(timestamp)
    set_created_time(image,timestamp)
    set_metadata_date_to_image_file(image,date)


def fix_folder(folder,level=0):
    print(f"{'\t'*level}Entrando en carpeta {folder}")
    subfolders = [f.path for f in os.scandir(folder) if f.is_dir()]
    
    for subfolder in subfolders:
        fix_folder(subfolder,level=(level+1))

    files = [f.path for f in os.scandir(folder) if f.is_file()]
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg')) and not re.search("\\._",file):
            fix_image(file,level=(level+1))

def configure_parser():
    parser = argparse.ArgumentParser(
        prog="Google Photos", 
        description="Solventa el problema con Google Fotos y los metadatos, ya que al descargar el Takeout windows pone la fecha de creación incorrecta"
    )
    
    parser.add_argument("-d","--directory",type=str,required=True)
    args = parser.parse_args()
    return args

if __name__ == "__main__":    
    args = configure_parser()
    
    if not os.path.exists(args.directory):
        print("No existe el path indicado")
        exit(-1)

    if not os.path.isdir(args.directory):
        print("No es un directorio")
        exit(-1)

    fix_folder(args.directory)