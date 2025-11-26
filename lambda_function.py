import boto3
import os
import uuid
import time
from PIL import Image
from io import BytesIO

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ImageMetadata')

def lambda_handler(event, context):

    start_time = time.time()

    try:
        source_bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        destination_bucket = os.environ['DEST_BUCKET']

        # Get image
        image_obj = s3.get_object(Bucket=source_bucket, Key=key)
        image_data = image_obj['Body'].read()
        image = Image.open(BytesIO(image_data))

        # Resize
        image = image.resize((200, 200))
        buffer = BytesIO()
        image.save(buffer, 'PNG')
        buffer.seek(0)

        resized_key = f"resized-{key}"
        s3.put_object(Bucket=destination_bucket, Key=resized_key, Body=buffer, ContentType='image/png')

        # Store metadata
        table.put_item(Item={
            'ImageID': str(uuid.uuid4()),
            'OriginalFile': key,
            'ResizedFile': resized_key,
            'Bucket': destination_bucket
        })

        latency = int((time.time() - start_time) * 1000)

        # ⭐⭐⭐ SUCCESS SLO LOG ⭐⭐⭐
        print({
            "status": "success",
            "status_code": 200,
            "latency_ms": latency,
            "file": key,
            "resized_file": resized_key
        })

        return {"status": "success", "resized_image": resized_key}

    except Exception as e:

        latency = int((time.time() - start_time) * 1000)

        # ⭐⭐⭐ ERROR SLO LOG ⭐⭐⭐
        print({
            "status": "error",
            "status_code": 500,
            "latency_ms": latency,
            "error_message": str(e),
            "file": key
        })

        raise e
