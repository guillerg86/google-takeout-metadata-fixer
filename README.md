# google-takeout-metadata-fixer

When download images from Google Takeout, some of this images have bad datetime on metadata. This script try to fix this using name of file or json file (provided by google)

Also this changes Windows "create time" metadata.

## Image accepted
- PNG
- JPEG
- JPG

## Formats accepted

For formats like

- IMG_20230728_223352\*
- IMG-20181205-WA\*
- 20230728_223352\*
- Screenshot_2019-04-09-09-30-17\*

script will take the datetime from the name and set on metadata (exif).

For the other formats, script will try to take JSON file. In this JSON file, Google, set 2 values with timestamp 

- CreatedTime
- photoTakenTime

First will use **photoTakenTime** unless there's more than 2 months (you can change on top on the script).

```
created_timestamp = float(metadata.get('creationTime').get('timestamp'))
phototaken_time = float(metadata.get('photoTakenTime').get('timestamp'))
if phototaken_time < created_timestamp and (created_timestamp-phototaken_time) < DIFF_BETWEEN_CREATEDTIME_PHOTOTAKENTIME_SECONDS:
	timestamp = phototaken_time
else:
	timestamp = created_timestamp 
```

## Usage

Just use `-d` to set the path where photos are stored. Script will check all subfolders inside this folder.

```
python.exe gphotos_metadata_fix.py -d "C:\Users\username\Desktop\MyGoogleTakeout"
```

## Metadata functions

### Exif metadata modify

```
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

```

### System data modify

```
def set_created_time(image,timestamp):
    setctime(image, timestamp)
    os.utime(image, (timestamp, timestamp))
```

