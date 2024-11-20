from django.conf import settings
from minio import Minio
from minio.error import S3Error

client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_USE_SSL
)

def process_file_upload(file, object_name):
    try:
        bucket_name = settings.MINIO_BUCKET_NAME
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)

        client.put_object(
            bucket_name,
            object_name,
            file,
            length=-1,
            part_size=10*1024*1024
        )

        url = client.presigned_get_object(bucket_name, object_name)
        return url
    except S3Error as e:
        return {'error': str(e)}