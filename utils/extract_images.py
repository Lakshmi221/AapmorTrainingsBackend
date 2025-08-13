from pptx import Presentation
from io import BytesIO
import cloudinary.uploader

def extract_slide_images(prs):
    slide_images = {}

    for slide_idx, slide in enumerate(prs.slides):
        images = []
        for shape in slide.shapes:
            if shape.shape_type == 13 and hasattr(shape, "image"):  
                image_blob = shape.image.blob
                buffer = BytesIO(image_blob)
                upload_result = cloudinary.uploader.upload(
                    buffer,
                    resource_type="image",
                    folder="training_slide_images",
                    public_id=f"slide_{slide_idx+1}_{shape.shape_id}",
                    overwrite=True
                )
                images.append(upload_result["secure_url"])

        if images:
            slide_images[slide_idx + 1] = images  

    return slide_images
