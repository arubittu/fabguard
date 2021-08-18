import json
import matplotlib.pyplot as plt
import PIL
from PIL import Image
from google.cloud import vision
import io
import os
import time
from shapely.geometry import Polygon
import pymongo
from pymongo import MongoClient
import boto3

#---------------
s3 = boto3.client('s3')
#---------------
def validate(pan_dict,adhar_dict):
    common_feilds=list(set.intersection(set(adhar_dict.keys()),set(pan_dict.keys())))
    validate_dict={}
    for entry in common_feilds:
        if pan_dict[entry]==adhar_dict[entry]:
            validate_dict[entry]=True
        else:
            validate_dict[entry]=False
    return validate_dict
#-----------------
def googleApi(img_path):
    # setting environment variable of g-cloud api 
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] ="enter google json doc name"
    # setting g cloud client
    start=time.time()
    client = vision.ImageAnnotatorClient()

    #with io.open(img_path, 'rb') as image_file:
        #content = image_file.read()
    content=img_path # img_bytes but i changed for now
    image = vision.Image(content=content)
    box_to_text={}
    # getting response from API
    response = client.text_detection(image=image)
    texts = response.text_annotations
    
   # adhar_copy3=plt.imread(img_path)
    print('Texts:')
    all_boxes=[]

    for text in texts:
        print('\n"{}"'.format(text.description))

        vertices = ([(vertex.x, vertex.y)
                    for vertex in text.bounding_poly.vertices])
        
        # extracting points from bbox
        (tl, tr, br, bl) = vertices
        tl = (int(tl[0]), int(tl[1]))
        tr = (int(tr[0]), int(tr[1]))
        br = (int(br[0]), int(br[1]))
        bl = (int(bl[0]), int(bl[1]))

        # drawing bbox on image
        #cv2.rectangle(adhar_copy3, tl, br, (255, 0, 0), 2)
    
        print('bounds: {}'.format(vertices))
        all_boxes.append(vertices)
        box_to_text[str(vertices)]=text.description

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    stop=time.time()
    print('time taked is {} seconds'.format(stop -start))
    return all_boxes,text,box_to_text#,adhar_copy3
#---------------------------
def preprocess_adhar(adhar_dict):
    adhar_dict['dob']=[adhar_dict['dob'][-1]]
    adhar_dict['gender']=[adhar_dict['gender'][-1]]
    return adhar_dict
#--------------------------

bbox_fields_pan={'name':[(60,160),(690,160),(690,200),(60,200)],
             'dob':[(61, 307), (252, 307), (252, 343), (61, 343)],
             'father_name':[(60,215),(690,215),(690,250),(60,250)],
             'pan_num':[(50, 405), (300, 405), (300, 455), (50, 455)]} # have to tweak the values

bbox_fields_adhar={'name':[(215,100),(340,100),(340,115),(215,115)],
             'dob':[(215,135),(460,135),(460,150),(215,150)],
             'gender':[(215,160),(340,160),(340,182),(215,182)],
             'adhar_num':[(215,280),(450,280),(450,320),(215,320)]} # have to tweak the values
  
def retreive_fields(bbox_fields,all_boxes,box_to_text,aspect_ratio=3.3/2.1):
    # we assume the image is aldready in proper aspect ratio
    # aspect ratio is ratio of lenght/bredth or x/y
    # bbox_feilds is the bounding boxes dictionary where we should look for our desired feild - is pre determined
    # all_boxes is all extracted bboxes from api
    # box_to_text is also extracted from googleapi functon which maps bbox to their text 
    #----
    #output is a dictionary , keys as feilds and values as their extracted texts

    #_-----------------------------
    output_dict={}
    # to retreive the boxes overlapping bbox_feilds
    for key,bbox in bbox_fields.items():

        (tl1, tr1, br1, bl1) = bbox # main bbox
        poly_1=Polygon(bbox) # main box

        if key not in output_dict.keys():
            output_dict[key]=[]
        for box in all_boxes:
            (tl2, tr2, br2, bl2) = box #
            poly_2=Polygon(box) #
            intersection=poly_1.intersection(poly_2).area
            area2=poly_2.area
            ratio = intersection/area2
            if ratio>=0.75: #only y condition added, consider adding x condition aswell
                output_dict[key].append(box_to_text[str(box)])

    return output_dict
#--------------------------
def bytes_to_ndarray(bytes):
    bytes_io = bytearray(bytes)
    img = Image.open(BytesIO(bytes_io()))
    return img
    
def lambda_handler(event,context):
    # get bucket and key names
    print(event)
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    try:
        # get adhar from s3
        response = s3.get_object(Bucket='fabgard', Key='test_img.jpg')
        image_bytes = response['Body'].read()
        # get pan from s3
        response2=s3.get_object(Bucket='fabgard', Key='test_img2.jpg')
        image_bytes2=response2['Body'].read()
        
        print(bucket,key)
        #Bucket = s3.Bucket(bucket)
        #object = Bucket.Object(key)
        #response = object.get()
        #file_stream = response['Body']
        #im = Image.open(file_stream)
        
        #rs=boto3.resource('s3')
        #Bucket=rs.Bucket(bucket)
        #object = Bucket.Object(key)
        #object.download_file('lol.jpg')
        #response.download_file('lol.jpg')
        #image_bytes=bytes_to_ndarray(image_bytes)
        print("CONTENT TYPE: " + response['ContentType'])
    #    return response['ContentType']
    except Exception as e:
        print(e)
        #print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
    #--------------- API google ocr 
    #image_bytes=Image.open(image_bytes)
    # for adhar
    all_boxes,text,box_to_text=googleApi(image_bytes)#('Aadhar_1.jpg') # removied ahdar3 variable that was also returned
    adhar_dict=retreive_fields(bbox_fields_adhar,all_boxes,box_to_text)
    adhar_dict=preprocess_adhar(adhar_dict)
    
    # for pan
    all_boxes_pan,text_pan,box_to_text_pan=googleApi(image_bytes2)
    pan_dict=retreive_fields(bbox_fields_pan,all_boxes_pan,box_to_text_pan)
    
    #----- mongo connect------------
    
    client = MongoClient("enter url")
    myDB = client['fabguard']
    mycollection = myDB.user
    
    # insert document/item in db
    item_to_insert={'adhar':adhar_dict,'pan':pan_dict}
    myDB.user.insert_one(item_to_insert)
    data = myDB.price.find({})
    
    # print and show
    for i in data:
        print(i)
    
    # close connection
    client.close()
    #---------for test purposes-------------
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
