from PIL import Image
import boto3
import io
import os
import uuid
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DDB_TABLE'])

def lambda_handler(event, context):
    source_bucket = os.environ['SOURCE_BUCKET']
    dest_bucket = os.environ['DEST_BUCKET']

    for record in event['Records']:
        key = record['s3']['object']['key']
        image_id = str(uuid.uuid4())

        # Download image
        response = s3.get_object(Bucket=source_bucket, Key=key)
        img = Image.open(response['Body'])

        # Resize
        img.thumbnail((300, 300))
        buffer = io.BytesIO()
        img.save(buffer, 'JPEG')
        buffer.seek(0)

        # Upload resized image
        resized_key = f"resized/{os.path.basename(key)}"
        s3.put_object(Bucket=dest_bucket, Key=resized_key, Body=buffer, ContentType='image/jpeg')

        # Store metadata
        table.put_item(Item={
            'image_id': image_id,
            'original_key': key,
            'resized_key': resized_key,
            'upload_time': datetime.utcnow().isoformat(),
            'source_bucket': source_bucket,
            'dest_bucket': dest_bucket
        })

    return {'statusCode': 200, 'body': 'Image resized and metadata stored successfully.'}




